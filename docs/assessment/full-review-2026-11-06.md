# Full review: scientific, technical, UI/UX

Date: 2026-11-06 · Base: `dev/m5b/corpus-import` at `a1e8811` (main at `87d4467`), plus the uncommitted corpus-import work where stated · Scope: everything merged since the kits became one package (PRs #181–#194) and the packaged app as it runs today.

How this was done: three independent passes. A methodological review of the screening method against PRISMA 2020 / PRISMA-ScR and AI-assisted-screening norms; an engineering review of the server, data integrity, tests, packaging and the in-progress import; and a hands-on walk of the packaged app (`nexus-scholar ui` from this checkout, on scratch copies of `golden-uav-30` and the 2026-11-06 evidence run, at 1440 px and 375 px, dark and light, `en` and `ar`). Every file:line cited was read at HEAD. Two findings were reproduced by running code (S-P0-1, the Prepare batch size).

## Verdict in six lines

1. **The human decision ledger is sound and ahead of most screening tools.** Append-only HUMAN-only decision events, no imputation on the production path, per-batch approval bound to byte digests, hashed protocol, journal on every step. The assessment findings CON-11, SRCH-16/17/35 and AGT-16/18/19 are genuinely fixed.
2. **Usable today for the title/abstract stage of a single-reviewer scoping review**, provided the corpus is merged and deduplicated outside the app first. The uncommitted multi-file import must not be used on the real review yet (S-P0-1).
3. **The AI layer is well designed but unmeasured**, and the planned measurement is against labels that were themselves produced by LLM arms and bulk-confirmed (S-P0-2). No recall figure from that gate belongs in the thesis.
4. **Engineering: shippable as a local beta.** No P0 security or data-loss defect found. The risks are silent correctness drift: publication status that ignores decision files, PRISMA content computed in two hand-synchronised copies, undefined names in `src/` that CI never lints, and no pytest on Windows in CI.
5. **UI: the right shape, the wrong friction.** Blinding, draft styling, consent gate, publish checks and export are well done. Prepare makes a promise the engine ignores, the methods paragraph repeats itself, exclusion reasons are bare codes, and 7 mandatory checklist answers per record will cost roughly 11,500 keypresses on the 1,644-record review.
6. **The golden run proves the pipeline and the audit trail, not blinding.** 29 of 30 decisions were made with the draft visible, so there is zero concordance evidence, and one generated methods sentence reads as if it were a blind measure.

---

## 1. Scientific review

### S-P0: would invalidate or misreport a review

**S-P0-1. Multi-file RIS import (working tree) publishes PRISMA counts that do not add up.** Reproduced with the branch's own fixture (two RIS files, 6 records → 4 studies, accept → prepare → events → approve → collect): the published `prisma_report.json` says `total_identified: 6, duplicates_removed: 0, records_screened: 4`. `scripts/check_golden_workspace.py` fails ("duplicates_removed is 0, the corpus snapshot gives 2"); the live preview says 2 (`src/scholar_harness/console/api/screening_v1.py:586,623`). The methods paragraph would print "6 records were identified; 0 duplicates were removed; 4 records were screened".
Cause: the import writes one `verified.json` row per raw record; the collector and the approval mirror both build `docs` from every row and compute `duplicates_removed = total_raw_harvested − len(docs)` (`src/scholar_harness/screening/collector.py:1182-1188`; `src/scholar_harness/authority/review.py:800-806`). Both copies agree with each other, so the wrong number is hashed, approved and published.
Fix: take `identified` and `duplicates_removed` from the accepted corpus snapshot (`len(record_to_study)`, `len(studies)`), as the preview and the check script already do, in **both** collect and `_compute_single_screener_content`; add a test that runs the two-RIS fixture through publish and asserts `prisma_report.json` equals `/prisma/preview` and the check script passes. Until then the Zotero workaround in `docs/assessment/prisma-scr-readiness.md` is the only safe path.

**S-P0-2. The prompt-gate "gold set" is not human-screened.** `src/scholar_agent/prompt_gate.py:10-11` calls it "every human-confirmed include of uav-crop-weed-v03". The v03 labels come from two agent arms, an agent third lane and an agent pass-2 (`workspaces/uav-crop-weed-v03/AMENDMENTS.md:70-80`: "a delegated mechanical decision, not authenticated human approval"; 14,150 decisions confirmed in one sweep, 0 changed). 346 "excludes" are no-abstract exclusions and 145 are title-only moderation excludes, which are label artefacts, not criterion judgements. The gate therefore measures Claude's agreement with earlier LLM labels, not sensitivity against human truth. `prisma-scr-readiness.md:55,97` tells the researcher to report "measured recall" in Limitations: that must not be done from this set.
Fix: build a real validation sample (300–500 records, stratified by v03 lane, dual-screened by two humans, κ reported), re-freeze the eval set on it, rename the current set "agent-labelled" in code and docs. Keep "recall" out of product text until then (the paragraph's `FORBIDDEN_WORDS`, `src/scholar_harness/screening/export.py:71`, already does this).

### S-P1: would be challenged by a Q1 reviewer

**S-P1-1. The golden run gives no blinding evidence, and the reveal sentence is misleading under `show`.** All 29 events carry `proposal_shown.revealed_after_decision: false`; settings changed four times (two are no-op show→show); 0 supersessions. The generated paragraph says "After seeing a draft, the reviewer changed 0 of 29 decisions" (`export.py:671-674`), which reads as a blind-then-reveal result when the draft was visible at decision time. The Agreement screen correctly says "29 records were decided with the draft already in view and are not counted", so the two surfaces disagree. The paragraph also emits one sentence per no-op settings row ("The AI-agreed-exclusion setting was off from 2026-11-06" three times, `export.py:690-695`).
Fix: when decisions were made with the draft visible, say "N decisions were made with the draft visible; no blind comparison is reported" and suppress "changed k of n"; collapse settings rows whose value did not change. Rerun the golden gate with blinding hidden so Agreement has data.

**S-P1-2. Methods paragraph gaps against PRISMA 2020 item 8/16a, PRISMA-ScR 9/14 and journal AI-use declarations.** What it says is accurate; what is missing:
- "provider not recorded" for MCP drafts (`export.py:581-599` reads run files only) although every proposal carries `driver: "mcp"`; say "via the researcher's Claude session (MCP)".
- No screening dates, no date of AI use, no model release date.
- No statement of what the model saw (title, abstract, year; no full text; no database) and that the outcome was derived by a versioned rule table (`rules_version` is stored, never reported).
- "a draft decision with quoted evidence for 29 of 30" overcounts: 6 of the 29 were Unclear with no evidence; report drafts by derived outcome.
- No count of records without an abstract (title-only screening is a sensitivity risk).
- The single-reviewer limitation is left to the author; `not_stated` should name it.

**S-P1-3. Checklist answers, outcome and reason code are never checked for consistency.** `src/scholar_harness/screening/events.py:240-243` validates only that an EXCLUDE's `reason_code` is a protocol code. Nothing checks that the code names a criterion the reviewer answered `no` (inclusion) or `yes` (exclusion), nor that an INCLUDE carries no failed criterion. PRISMA reason counts therefore come from the chip, not the checklist. One reason per exclusion is enforced and FAILS-INC-n is counted as its own reason (fixed in M5-slim).
Fix: an engine rule `REASON_CODE_INCONSISTENT`; optionally derive the reason as the first failed criterion in protocol order and let the reviewer override with a note (this also fixes U-4 below).

**S-P1-4. The MCP-route prompt gate is not leak-proof and is not an evaluation of the shipped driver.** The prompt-gate default workspace is `workspaces/uav-crop-weed-v03`, which holds every label on disk, and the answering Claude Code subagents run in this repository. Nothing prevents them reading the labels and nothing records what they could read. The eval set's prevalence (644 includes to 1,000 excludes, about 39 %) is far from v03's (about 4.5 %), so "exclusion rate" must not be read as workload saved.
Fix: run the answering agent in a worktree without `workspaces/` and record its tool scope in the report; prefer the API driver when credit exists; report prevalence next to every rate.

**S-P1-5. Second screener and κ.** CON-10/14/15 are fixed in the collector's dual path (`collector.py:373-386, 463-476, 693-700`), but `review.py:661-668` refuses dual inputs (`REVIEW_DUAL_UNSUPPORTED`), so a dual screening can never be approved or published. `/agreement` returns `kappa: null` with a note (correct). `calculate_fleiss_kappa` still returns `1.0` when expected agreement is 1 (`scholar_search/screening.py:825-826`), which is undefined, not perfect. There is no CI on `agreement_pct`.
What a methodologist needs: a second human, blind to the first and to the AI, on a random sample (10–20 % or all), Cohen's κ (3-category and INCLUDE+UNCLEAR vs EXCLUDE) with 95 % CI and raw agreement, a pre-specified resolution rule recorded as events, and a calibration pilot of about 50 records. Honest single-reviewer wording for the thesis: "Title/abstract screening was performed by a single reviewer (MB). No second reviewer or inter-rater agreement was measured; a large-language-model draft (model, prompt hash) was available as an advisory aid and every decision was made by the reviewer. Single-reviewer screening is associated with missed eligible studies (Waffenschmidt et al., 2019); this is a limitation of the review."

### S-P2: methodological polish

- Legacy `POST /batch/{n}/decisions` is still mounted and in the browser allowlist (`src/scholar_harness/console/browser.py:43`) with `method` defaulting to `HUMAN` and client-settable (`console/api/screening.py:47-50`). Remove it from the allowlist or require `method`.
- The legacy Gemini path substitutes heuristic decisions on JSON failure (`scholar_search/screening.py:571,629`) instead of routing to a person; mark it parked or map the fallback to MAYBE.
- CON-13: `contracts/acceptance.py:433` checks the batch id only when exactly one `screening_batch` parent is present; no explicit refusal of more than one.
- `conflicts_flagged` in `prisma_report.json` is a model-confidence artefact, always 0 for human decisions; drop it.
- `check_golden_workspace.py` arithmetic is sound. It does not check reason codes against the protocol, the manifest's `total_raw_harvested` against the snapshot, or journal `SCREENING_DECISIONS_RECEIVED` counts against stored events.
- The screening prompt is sound (per-criterion yes/no/not_reported with a verbatim quote, record wrapped as data, no label leakage, model never chooses the outcome, any `not_reported` → MAYBE, refusal/truncation → Unclear). Weakness: `no` on an exclusion criterion requires the abstract to state it does not apply, which abstracts rarely do, so the Unclear rate will be high on real corpora (6 of 29 on the curated golden set). Consider a protocol-declared absence-of-evidence policy per exclusion criterion, applied in code and reported in methods.
- The import's `searched_on` and `query` are optional; PRISMA-S needs both per database. No per-database unique-after-dedup or overlap table is produced (recoverable from `source_database` + `record_to_study`).

### Strong, keep

Append-only idempotent client-minted events with engine stamps; proposals as a separate store with a versioned rule table and verbatim-quote validator; blinding default on with reveals journaled before display and `changed_after_reveal` stamped by the engine; byte-bound approval and publication digests; the facts-only methods paragraph with `figures`, `sources`, `caveats`, `not_stated` and forbidden words; a frozen, hash-checked eval set with a Wilson bound and a stated bar; `check_golden_workspace.py` as an executable gate.

---

## 2. Technical review

### T-P0: none found

Probed specifically: arbitrary command execution from any route, path traversal on workspace open/create, token leakage to the browser, and silent alteration of a published generation. None reproduced.

### T-P1: will bite within weeks

**T-P1-1. `require_current_generation` binds outputs but not decision files** (known, deferred). `authority/generations.py:1269-1300` checks only `PUBLICATION_OUTPUTS` digests; a decision event after publish leaves the status CURRENT. `screening/export.py:183` and `/summary` (`screening_v1.py:614`) each bolt on `stale_projections`; `/ui/publication-status` (`console/api/workspace.py:690`) does not, and that is what the Home and Export links use. Fix: put `stale_projections` inside the gate and return `GENERATION_STALE` with `stale_batches`. Needs the contract decision the milestone file already asks for. Effort M.

**T-P1-2. Publication content computed twice.** `authority/review.py:618` vs `screening/collector.py:1245`. The FAILS-INC-01 divergence already bit once and both copies now share S-P0-1. Fix: one `publication_content(ws, batch)` helper imported by both, plus a parity test over varied rows. Effort S.

**T-P1-3. Undefined names in reachable code; CI lints only `scripts/`.** `uv run ruff check src/ --select F821,B023,F811`: `screening/report.py:51-52` (`agent_screen.py calibrate` without a gold file raises NameError), `scholar_verify/cli.py:247,251` (`re` not imported), `console/api/screening.py:1206` (`logger`), `inception/grounded.py:253` (`Responder`), `integrations/latex_typst.py:97` (loop-variable capture). Overall `ruff check src/`: 618 findings (B008 101, BLE001 95, F401 59, I001 53, S110 try-except-pass 36). Fix: add `ruff check src/ --select F,B023,B006,E9` to `ci.yml:77` now. Effort XS–S.

**T-P1-4. Job subprocesses import from the workspace folder and inherit the console token.** `runtimes/actions.py:274-277` runs `[sys.executable, "-m", "scholar_harness.agent_screen", ...]`; `job_runner.py:168-172` runs it with `cwd=workspace` and no `env=`. With `-m`, `sys.path[0]` is the cwd, so a `json.py` or `scholar_harness/` folder inside a shared workspace zip executes on Prepare. The same spawn passes `NEXUS_CONSOLE_TOKEN` through. Fix: add `-P` to the argv and strip the token from `env`. Effort XS.

**T-P1-5. No pytest on Windows in CI.** `.github/workflows/ci.yml:103-131` runs the full suite on ubuntu/3.12 only; Windows gets lint, manifest, wheel `--help` and `wheel-e2e`. The Windows-specific code (`events.py:162-174` msvcrt lock, `generations.py:548-571` CRLF digests, `catalog.py:215-222` MAX_PATH cleanup) is verified only by the researcher's local 20-minute run. Fix: a Windows job over `tests/console tests/authority tests/test_screening_* tests/cli`. Effort S.

**T-P1-6. Version frozen at 1.0.0 while classified Beta.** `pyproject.toml:7,26`; `release.yml` hardcodes the 1.0.0 wheel and `.mcpb` names, so every tag ships the same version and `uv tool install` cannot see an upgrade. Fix: `hatch-vcs` or bump per tag and derive file names from `pyproject`. Effort S.

### T-P2: debt

- `/healthz` returns the absolute workspace path before authentication (`serve.py:49, 243-245`). XS.
- Argument injection into kit CLIs for a desktop-token holder: `actions.py:217-220` substitutes `{q}` without `--`; `pipeline_executor.py:190-199` appends arbitrary `--key value` from a saved spec. Not browser-reachable. XS/S.
- Settings, operator context and batch approvals are written non-atomically (`screening_v1.py:379, 466`; `review.py:931-935`); torn files fail safe but need manual repair. `generations.py:538-575` already has tmp+rename helpers. S.
- `os.replace` on Windows is unretried (`generations.py:575`, `pipelines.py:414`, `mcp_setup.py:203`); antivirus holds surface as 500s. XS.
- Publication digests are platform-dependent by design (`generations.py:548-571` hashes with `os.linesep`), so reproducibility holds per host, not across hosts. Document; a fix needs a contract decision. M.
- Gate selection gaps: an untracked `.claude/launch.json` makes `select_test_gate.py --changed main --stage inner` return the full suite; `corpus_accept.py` falls into `harness-other`, whose inner gate never runs `tests/cli/test_accept_corpus.py` or `tests/console/test_corpus_api.py`. XS.
- No coverage measurement anywhere. The 20-minute suite is I/O- and spawn-bound (27 files start a server, 19 spawn subprocesses). S.
- Dead code: six `/ui/*` console routes with no caller (`console/api/screening.py:787,1037,1186`; `workspace.py:445,614,922`) and 10 of 16 exported client functions in `lib/screening-api.ts`. S.
- MCP network transports pin no host (`scholar_agent/server.py:2399`); loopback only by SDK default. XS.
- Base install carries parked-kit weight (scipy, networkx, pyvis, pypdf, bibtexparser, three HTTP stacks). `--help` is proven in CI; this is size, not breakage. M.
- Threat-model statement to write: `generation.json` and approvals are digest-bound but unsigned, and the journal is append-only but not hash-chained. Fine for a single-researcher local tool; say so in `docs/data-flow.md`.

### The in-progress corpus import (uncommitted, 9 files)

Good: typed refusals with HTTP mapping, 50 MB cap, sha256 duplicate-file detection, frozen after acceptance, every step journaled, preview and acceptance share the same `Deduplicator`, allowlists updated on both sides with the equality test, tests on three layers. Lane STANDARD is right (no change under `contracts/`).

Fix before merge, in addition to S-P0-1:
1. Non-atomic writes in stage and `_materialise_staged`; a crash leaves `verified.json` without a manifest and the next stage refuses `VERIFIED_EXISTS` with a misleading message. XS.
2. Orphaned file on parse failure in `stage_ris_source` (bytes written before `_parse_ris`). XS.
3. The provenance manifest is not lineage-bound: it can be edited after acceptance and nothing refuses. Record its sha256 in the acceptance event and registry metadata and have `build_methods` compare. S.
4. "Byte for byte" is not true over the API: `CorpusSourceBody.content: str` re-encodes as UTF-8, so a Latin-1 or UTF-16 export (Web of Science does this) is altered and its sha256 differs. Base64 or multipart. S.
5. `_stable_sci_id` includes file position, and `verified.json` order equals staging order, so staging the same files in another order yields a different run id. Sort by label or document it. XS.
6. Corrupt `artifact_registry.json` → bare `json.loads` 500. XS.
7. Missing tests: CLI ↔ API parity on `artifact_id`, a CRLF RIS fixture, a gate-manifest area; gitignore `.claude/launch.json`.

### Well engineered

`screening/events.py` (commit-or-rollback of events plus journal row, projection under the same lock, idempotency, order-independent winners); `authority/generations.py` (downgrade prevention, mixed-generation detection, tmp+rename staging with cleanup); `console/browser.py` + `serve.py` (single-use launch code, cookie never carries the token, Host/Origin/`Sec-Fetch-Site` checks, phone scope, allowlist equality test); path containment in `workspace/catalog.py` and `scholar_agent/server.py`; keys never in files, keychain read at server start, `.mcpb` without secrets; the milestone records with reproducing-test tables and the CI wheel smoke.

---

## 3. UI/UX critique

Walked live. Screens: Workspaces, Home, Prepare, Agent proposals, Triage, Agreement, Publish, Export.

### Defects, in order of harm

**U-1. Prepare promises a batch size the engine ignores.** The field reads 20; set to 10, the confirm dialog says "Prepare batches of 10 records?", the engine produces 20 + 10. `POST /prepare` reads `batch_size` (`screening_v1.py:558`) and then starts `screen_prepare` with no argument. On the one screen whose job is trust, this is a false promise. Either pass the size through or remove the field until it works.

**U-2. The methods paragraph is not pasteable.** Setting history is dumped as repeated sentences ("Drafts were shown before the decision from 2026-11-06." twice, "The AI-agreed-exclusion setting was off from 2026-11-06." four times), "provider not recorded" sits inside a manuscript sentence, and "changed 0 of 29 decisions" appears when drafts were visible (see S-P1-1). The "Draft · check before you submit" label is honest, but a researcher will have to rewrite most of it.

**U-3. The workspaces list calls a published workspace "Screening in progress."** The status is keyed from the last journal action, not from the publication status (`components/workspaces-screen.tsx:45`). The current workspace's "Open now" badge renders as a wrapped two-line pseudo-button in the Action column.

**U-4. Exclusion reasons are bare codes.** The reason picker shows "1. EXC-01 … 7. FAILS-INC-03" with no label, against the brand rule "plain words first, raw value underneath". Spec 03 promised a "From your answers: Exclude (fails INC-01)" line from the rule table; it is not there, so after answering INC-01 = No the reviewer still has to find FAILS-INC-01 by memory. Fixing S-P1-3 and pre-selecting the first failed criterion removes most of this.

**U-5. The checklist tax.** Seven answers are required before any decision. On the 1,644-record review that is about 11,500 keypresses before 1,644 decisions. The keyboard path works well (1/2/3 advance focus, I/E/U, reason 1–7 + Enter, "Decision saved" announced), but after deciding, N is still needed to advance even when there is no draft to reveal. Consider: answer-until-decisive (stop at the first failed criterion for an Exclude), an auto-advance setting, and a "no draft, advance on decide" shortcut.

**U-6. Undo is shown but refuses on a first decision** ("A first decision cannot be undone; change it instead."). A visible control that refuses is worse than a hidden one; hide Undo until there is a prior event, or let a retraction be an event.

**U-7. All-decided triage is a dead screen.** The centre column is empty; the right aside still says "Hidden until you decide" with skeleton bars; the subtitle still says "The agent's draft is shown beside each record (your setting)".

**U-8. The queue is a flat list with no position.** Thirty titles with "no proposal" under each; no "12 of 30", no batch grouping, no search, 50 per page by cursor. At 1,644 records this is where the reviewer will live for weeks.

**U-9. Console noise on every page.** React error #418 (hydration mismatch) on load, and one 404 per navigation for `__next.$d$locale…__PAGE__.txt` prefetch files the static export does not have. Harmless to the user, but hydration mismatches can flicker and they hide real errors.

**U-10. No workspace name anywhere in the screening screens** (deferred in M5-slim). With two workspaces of the same title in the list, the only differentiator is a 120-character path.

**U-11. Phone (375 px).** The step bar wraps to three rows and the queue card fills the first screen; the record is below the fold. Spec 04 (swipe card) is M2, but the stacked desktop layout should at least collapse the queue.

**U-12. Approval by terminal code.** By design until phone pairing, but for a solo user on the packaged app this is the most awkward step: the guide says to keep the terminal open, and the user has gone to the browser.

**U-13. Small things.** Home shows the raw code `NOT_PREPARED` in the state card and a "Run from the terminal" block with `uv run python src/scholar_harness/agent_screen.py prepare <workspace>`, which only works from a source checkout. Criterion INC-03 carries operational text ("Screened under Option C (single lead reviewer Mouadh Bekhouche …)") shown verbatim on every record: a protocol-authoring issue the triage surface amplifies (7 criteria × about 60 words is a screen of text before the abstract).

### What works

Blinding default and the draft styled as a draft (dashed, plain surface, "Not a decision"); the provenance line under every decision ("Recorded as you · HUMAN · time · protocol sha"); the Publish checks list with five named checks and the failing count; the PRISMA preview labelled "Preview · not written"; the consent gate on Agent proposals with what leaves the machine, a cost estimate and a ceiling, and "Check the agent on your labels first"; the Export screen's generation fingerprint and reference-manager instructions; every UI decision landing in the journal as `SCREENING_DECISIONS_RECEIVED` with event ids; light and dark both legible with self-hosted fonts; Arabic mirrored correctly with Arabic-Indic numerals; the footer sentence "Runs on this computer. Nothing is sent anywhere unless you start agent proposals."

---

## 4. Priorities for the next four weeks

1. **Identification integrity before the real review** (S-P0-1, T-P1-2, import fixes 1–4). One source of truth for identified / per-database / duplicates / screened, used by collect, approval, preview, check script and methods; an end-to-end test from two RIS files to the published report. Required before `accept-corpus` runs on the PhD corpus, because the snapshot freezes at acceptance.
2. **Honest AI reporting** (S-P0-2, S-P1-1, S-P1-2, U-2). Rename the v03 set agent-labelled; plan a dual-human validation sample; fix the reveal sentence, collapse settings history, add provider, dates, what the model saw and the rule-table version; rerun the golden gate blind.
3. **Currentness and lint gates** (T-P1-1, T-P1-3, T-P1-4). `stale_projections` inside the gate; `ruff --select F` on `src/` in CI with the eight real bugs fixed; `-P` and a token-stripped env on job spawns.
4. **Triage ergonomics for 1,644 records** (U-1, U-4, U-5, U-8, S-P1-3). Pass the batch size through, derive the exclusion reason from the checklist, label the codes, add position and an advance-on-decide option.
5. **Windows in CI and a visible version** (T-P1-5, T-P1-6).

Then the second-screener lane (S-P1-5) as the next milestone: it is what a Q1 reviewer will ask for first.
