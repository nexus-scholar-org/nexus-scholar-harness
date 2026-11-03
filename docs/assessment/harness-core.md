# Harness core assessment — 2026-11-03

Status: independent assessment, read-only. Commit 5deb3a1. Scope: `src/scholar_harness/*.py` (≈7.5k lines: cli, orchestrator, pipeline_executor, agent_screen, agent_extract, extraction_adapter/producer, handoff, index_acceptance, doctor, mcp_setup, audit_log, rescreen_workspace, verification_identity), `src/scholar_harness/pipeline/` (≈3.4k), `workspace/` (≈1.9k), `integrations/` (≈0.65k), `skills_portability/` (≈0.85k); ≈14.3k lines total. Method: read the coordinator and every pipeline stage end to end, the CLI `run`/`sync`/`export`/`supervise` paths, the audit writers, handoff, executor and integrations; followed calls into `screening/batcher.py` and the search/rag kits only where the harness depends on their behaviour. Wrote and ran 12 offline repro scripts (scratchpad, `uv run python …`; network stages replaced by fakes, real harness code otherwise) and ran the targeted suites `tests/unit/test_coordinator.py test_discovery_stage.py test_verification_stage.py test_screening_prepare_stage.py test_cli_pipeline_summary.py tests/test_handoff.py` (124 passed). No files other than this one were modified.

## 1. Verdict

The harness core has been carefully decomposed into neutral stages, and its status vocabulary (fail-closed discovery, `PARTIAL`/`EMPTY_RESULT`, explicit SKIPPED reasons) is better than most research tooling. But the decomposition is mostly a verbatim move of the old orchestrator plus test seams. The classic `scholar-harness run` pipeline and the Contract v1 acceptance chain are two half-joined systems. On a fresh workspace `run` exits with code 1 before the screening handoff. Every re-run repeats the search and renumbers record identities. If indexing fails, matrix extraction and synthesis still run, and the run is logged `SUCCESS`. Several outputs claim more than the code measures: `verified.json` contains records that failed verification, and the search audit row omits the query string. A systematic review run through this path today could not be reproduced from its audit trail. The 124 passing tests do not catch these problems, because they replace exactly the stage joints where the defects live with fakes.

| Lens | Rating | One-line reason |
|---|---|---|
| Code quality & architecture | Weak | Clean stage split, but the pipeline is not a closed loop (out-of-band acceptance needed twice), it cannot resume, state is split across two vector stores and three phase models, and test-seam preservation leaves known defects in place (`MinimalIndexer` ×7, hash event IDs). |
| Correctness & bugs | Weak | 15 confirmed defects, 13 of them reproduced: silent SUCCESS after an index failure, identity collision in the DOI bridge, unverified records published as verified, the wrong default protocol path, and pipeline templates that cannot run. |
| Research-method fitness | Weak | Real guardrails (screening pause, generation gate, refusal quarantine), but no PRISMA-S-grade search log, nondeterministic record identity across runs, a legacy bypass of authorized screening, and synthesis/verification labels that overstate. |

## 2. Architecture and code quality

**CORE-01 — High — The classic pipeline cannot complete without out-of-band steps, and it cannot resume.** Static, with the consequences reproduced in CORE-07 and CORE-08.
- Stage 4 calls `cmd_prepare` (`pipeline/screening_prepare.py:195`). `cmd_prepare` requires an accepted `corpus_snapshot` in `audit/artifact_registry.json` (`screening/batcher.py:198-224`). No harness module builds or accepts one: grepping `src/scholar_harness` for `build_corpus_snapshot_artifact` finds nothing, and the kit producer `scholar_search/identity.py:308` is never called from the pipeline.
- Stage 6 requires an accepted `document_manifest` (`pipeline/indexing.py:572-616`). Only `extract publish` creates one (`cli.py:354-356`, `agent_extract.py:103`). The coordinator never calls `publish_document_manifest`.
- The coordinator always starts at Stage 1 (`pipeline/coordinator.py:310-314`). There is no "resume after collect" entry point, so continuing past screening means re-running the search (see CORE-06).

**CORE-02 — Medium — The architecture is shaped around preserving monkeypatch seams, not around correctness.** Static.
- `orchestrator.py:36-57` keeps a dead `ScholarIndexer` class that "exists only to allow existing tests to monkeypatch it".
- `orchestrator.py:65-148` re-exports private stage symbols (`_resolve_providers`, `_study_doi`) with `noqa: F401`.
- `mock_mode` is "accepted-but-unused" (`coordinator.py:264-267`).
- `run_indexing` defines an identical `MinimalIndexer` class seven times (`pipeline/indexing.py:544, 590, 661, 802, 819, 842, 885`). Each copy hard-codes `all-MiniLM-L6-v2` rather than reading the embedder that was actually used.
- `indexing.py:726-737` contains a dead `[... for r in result.rejected_documents] if False else []`. `indexing.py:755` publishes `"chunks": "0"` for every indexed document, with the comment "Would need to query the backend".
- Docstrings repeatedly state "verbatim move … no behavior change" (coordinator, every stage). The refactor therefore deliberately carried defects forward, for example the hash event IDs in `workspace/audit.py:14-19`, which say "Do not normalize it".

**CORE-03 — Medium — State is split-brained.** Static, partly reproduced.
- Two vector stores. The pipeline indexes into `<ws>/chroma_db` (`coordinator.py:290`). `extract index` uses `rag/chroma_db` (`extraction_producer.py:153`), and `sync_state` counts only `rag/chroma_db` (`orchestrator.py:439`). So `vector_chunks` in `project.json` never reflects a pipeline index, while `get_status` checks both (`orchestrator.py:288-290`).
- Three incompatible phase models:
  - `get_status` sets `PHASE_1_HARVESTING` when `included.json` exists, and `PHASE_3_COMPLETE` when any review longer than 50 characters exists (`orchestrator.py:233-311`).
  - `sync_state` sets `PHASE_4_COMPLETE` from a PRISMA key (`orchestrator.py:469-477`).
  - `handoff.HandoffPhase` uses trigger files the pipeline never writes: `literature/extraction/merged/records.json` and `synthesis/consensus.json` (`handoff.py:60-70`). The pipeline writes `extracted/*.md` and `synthesis/literature_review.md`.

**CORE-04 — Low — Two audit writers with different schemas share one ledger, and neither is tamper-evident.** Static.
- `append_event` uppercases action and status, uses UUID-based IDs, fills `parameters`, and updates `project.json` (`workspace/audit.py:144-210`).
- `append_legacy_event`, used by the coordinator, hydration, verification, indexing and the supervisor, does none of this: `parameters` is always `{}`, there is no manifest projection, and IDs come from `hash()` (`workspace/audit.py:229-270`).
- AGENTS.md's rule that every step must "reflect in project.json/INDEX.md" therefore does not hold for pipeline rows.
- Neither writer chains hashes, so the journal is append-only by convention, not verifiably.

**CORE-05 — Low — Harness/kit coupling is inconsistent.**
- The verification stage calls the kit verifier and then throws away its per-record verification log (`pipeline/verification.py:98-100`; `audit` is never read).
- The integrations hand-parse included records with their own key guesses (`integrations/zotero.py:37-40`, `obsidian.py:32-36`) instead of the `_study_doi` helper the pipeline already has (`pipeline/extraction.py:55-56`). See CORE-15.

## 3. Correctness and bugs

**CORE-06 — Critical — Every run re-searches and renumbers record identities. Screening batches join abstracts by those identities, so a re-run can attach another paper's abstract to a candidate.** Components reproduced; the end-to-end chain is static.
- *Evidence, part 1: identities depend on arrival order.*
  - The kit runs providers concurrently and appends documents as pages arrive (`scholar_search/engine.py:50-63`, `asyncio.gather`).
  - Dedup assigns `SCI-{cluster_index:06d}` in arrival order (`scholar_search/dedup.py:109-111`).
  - Reproduced: deduplicating the same two documents in reversed order swaps their IDs. `run1 [('10.1/a','SCI-000001'),('10.1/b','SCI-000002')]`, `run2 [('10.1/a','SCI-000002'),('10.1/b','SCI-000001')]`.
- *Evidence, part 2: the join.*
  - The accepted corpus snapshot records `alias_ids` as the SCI IDs from the dedup run it was built from (`scholar_search/identity.py:327-355`).
  - `cmd_prepare` builds candidates from that snapshot, but looks up abstracts by alias in the *current* `literature/verified.json` (`screening/batcher.py:244-263`).
  - The coordinator rewrites `raw_search.json`, `deduped.json` and `verified.json` on every run (`pipeline/discovery.py:413-414`, `pipeline/deduplication.py:80`, `pipeline/verification.py:144`), immediately before calling `cmd_prepare(force=True)` (`coordinator.py:444-446`).
  - So after any second run, `SCI-000005` in the snapshot can name a different paper than `SCI-000005` in `verified.json`, and that paper's abstract goes into the screening batch. Nothing checks that title and abstract belong together.
- *Impact.* Screening decisions can be made against the wrong abstract, silently. The re-run also overwrites the raw corpus that was actually screened, and adds a second `DISCOVERY_SEARCH` row whose counts describe a different harvest. The documented path forces this re-run: the only way to reach stages 5–9 is to run `run` again after `collect`.

**CORE-07 — High — `scholar-harness run` dies before the screening handoff on any workspace without a pre-accepted corpus snapshot.** Reproduced.
- Command: `repro_pipeline.py` fakes discovery, dedup, hydration and verification, and keeps the real screening preparation.
- Output: `No artifact registry found. Accept a corpus snapshot first.` / `SystemExit 1` / `registry exists: False`.
- `cmd_prepare` calls `sys.exit(1)` (`screening/batcher.py:198-200`), and `screening_prepare.py:117-119` deliberately propagates it. The CLI `run` (`cli.py:826-829`) does not catch it.
- *Impact.* No summary panel and no `PIPELINE_RUN_PAUSED`/`ABORTED` row. The journal ends on `VERIFICATION_IDENTITY_RESOLVED SUCCESS`, a gap in the audit trail. The README-level workflow (run, then screen, then collect) cannot be followed on a fresh workspace.

**CORE-08 — High — A failed Stage 6 does not stop matrix extraction or synthesis, and the run is recorded `SUCCESS`.** Reproduced.
- Command: `repro_index_fail.py` uses an `indexing_fn` that returns `status: FAILED`.
- Output: `pipeline status: SUCCESS`; order `[... 'extraction', 'matrix', 'graph', 'synthesis']`; `indexing: FAILED | synthesis: {'verified_claims': 1, ...}`; last journal row `PIPELINE_RUN_COMPLETED SUCCESS`.
- The coordinator never reads `index_res["status"]` (`coordinator.py:569-629`), and `_ledger_status` looks only at discovery (`coordinator.py:207-211`).
- Combined with CORE-01, Stage 6 always refuses inside `run`: no manifest is ever published. Stages 7 and 9 then query `chroma_db/`. That store is either empty, or left over from an earlier generation with a different included set.
- *Impact.* The synthesis matrix and `literature_review.md` can be built from a stale or empty index, and the run is announced "Completed Successfully".

**CORE-09 — High — `verified.json` and the "verified" count include records the verifier rejected.** Reproduced.
- The kit returns every input document. Failures come back as `(False, original_doc, "Unverified: …")` (`scholar_search/verifier.py:145, 217-237`).
- The harness drops the verification flags (`pipeline/verification.py:98`; `audit` is unused). It labels as "verified" every record whose identity resolved (`verification.py:112-115, 219`).
- Command: `repro_verify.py`, where the verifier reports `verified: False` for a record with a fabricated DOI.
- Output: `status SUCCESS verified 1`; `verified.json rows 1`, with no verification field; journal metrics `{'verified': 1, 'status': 'SUCCESS'}`.
- *Impact.* Records whose existence was never confirmed by Crossref or OpenAlex, including possible hallucinated or garbled citations from agent imports, are indistinguishable downstream from confirmed ones.

**CORE-10 — High — The DOI bridge can assign one study's identity to another study, silently.** Reproduced.
- The verifier replaces a record with a freshly normalised Crossref or OpenAlex record (`workspace_id=None`) on a title match of 0.90 or more (`scholar_search/verifier.py:106-141`).
- The harness then restores identity from whatever DOI that new record carries (`pipeline/verification.py:116-120`; bridge in `verification_identity.py:70-102`).
- Command: `repro_bridge.py`. Record A (`SCI-000001`, a preprint without a DOI) is title-matched to the journal version, which carries B's DOI. B is `SCI-000002`.
- Output: `status SUCCESS refused 0 ids ['SCI-000002', 'SCI-000002']`.
- *Impact.* A disappears without being quarantined, B appears twice, and the refusal accounting reports nothing. This is a realistic case: the preprint and journal versions that dedup did not merge.

**CORE-11 — Medium — `run` without `-p` reads `protocol.json` from the current directory, not the workspace. Screening always uses the workspace protocol.** Reproduced.
- `cli.py:820` sets `protocol_path = protocol or Path("protocol.json")`, so the coordinator's own default `ws/"protocol.json"` (`coordinator.py:270`) never applies.
- Command: `repro_cli_proto.py`, running `run -w <ws>` from another directory.
- Output: `exit 1 exc: FileNotFoundError Protocol file not found at C:\…\tmp07l4hjie\protocol.json`, which is the CWD, not the workspace.
- Run from the repo root next to some other `protocol.json`, the search compiles from that file, while `cmd_prepare` validates against `<ws>/protocol.json` (`screening/batcher.py:192, 231-236`). The search protocol and the screening protocol can differ.

**CORE-12 — Medium — An unauthorized `included.json` drives stages 5–9, with only a log warning.** Reproduced.
- In `repro_index_fail.py`, a hand-written `included.json` with no screening generation produced `PRISMA outputs are LEGACY_UNVERIFIED … proceeding` on the logger. Extraction, matrix and synthesis then ran, with pipeline status `SUCCESS`.
- `coordinator.py:495-502` only logs. Nothing is added to `results` or to the `COMPLETED` ledger row.
- *Impact.* The AG-03C authorization gate can be bypassed by any workspace that never created authorized material. The output does not carry the `LEGACY_UNVERIFIED` code that the comment promises to "report explicitly".

**CORE-13 — Medium — The supervisor skips phases and marks unmet phases complete.** Reproduced.
- Command: a workspace containing only `literature/knowledge_graph.json` (no `intent.json`, no `included.json`), then `run_supervisor_once`.
- Output: `{'action': 'ADVANCED', 'from_phase': 'INCEPTION', 'to_phase': 'SYNTHESIS', 'completed_phases': ['INCEPTION']}`, journal status `['SUCCESS']`.
- `next_actionable_phase` steps over phases whose triggers are missing (`handoff.py:232-245`). `advance_phase` marks the current phase complete without checking its trigger (`handoff.py:159-165`).

**CORE-14 — Medium — The PipelineSpec executor (`run --pipeline`) cannot run its own gallery templates and misreports failures.**
- *Reproduced: the templates call commands that do not exist.* All five built-in templates pass `validate_spec`. Each first node renders as `uv run scholar-search run --query …`, and `scholar-search --help` lists no `run` command. Each screening node renders `agent_screen.py prepare --workspace <slug>`. Running that gives `agent_screen.py: error: unrecognized arguments: --workspace`, because `workspace` is positional (`agent_screen.py:89-90`; templates at `console/api/pipelines.py:87-113`; argv built in `pipeline_executor.py:178-199`).
- *Reproduced: embedded templates pass through unresolved.* `resolve_template('workspaces/{{ws}}/literature', …)` returns `'workspaces/{{ws}}/literature'` unchanged (`pipeline_executor.py:123-125`), but validation accepts it (`pipeline/validation.py:34-37, 101-104`).
- *Static: idempotency checks existence only.* A node is skipped whenever its outputs exist (`pipeline_executor.py:247-254`), although the module docstring promises a fingerprint check (`:15-16`). Outputs from a different query or protocol are silently reused.
- *Static: failures are reported as completion.* With `on_fail=continue`, downstream nodes still receive the failed node's outputs (`:329-335`). The CLI prints "PipelineSpec execution complete" and exits 0 whenever no node `halted` (`cli.py:876-881`).
- *Static: decision files.* `requires_decision` counts any `batch_*_decisions.json` file as a decision, even `[]` (`:218-223`).
- *Static: no audit trail.* The executor writes no journal rows at all.

**CORE-15 — Medium — Zotero and Obsidian exports drop DOIs from real included records and mislabel what they did.** Reproduced.
- Real `included.json` rows are `asdict(Document)`, so the DOI sits at `external_ids.doi` (`scholar_search/screening.py:471-473`). The exporters read the top-level `doi` key (`zotero.py:38`, `obsidian.py:32, 36`).
- Command: an inline script using a real `Document` row.
- Output: `mode LIVE_API | DOI '' | date None | pdf None`.
- `sync_mode` reports `LIVE_API` whenever keys are set, although no API call exists (`zotero.py:87`). The CLI prints "✅ Synced N items to Zotero collection" (`cli.py:967`).
- The `p.get("year", 2024)` default (`zotero.py:39`, `obsidian.py:35`) fabricates a year when the key is absent, and writes `"None"` when the key is present but null.
- `obsidian.py:55-57` writes unescaped titles into YAML, so a title containing a quote breaks the note.
- The integration tests use a fixture with a top-level `doi` (`tests/integrations/test_integrations.py:26, 34`) that does not match the real row shape, which is why they pass.

**CORE-16 — Medium — `sync` publishes PRISMA-like counts from guessed filenames and turns unreadable artifacts into 0.** Reproduced.
- Command: a workspace containing only `calibration/included_gold_sample.json` (20 records) and `calibration/papers_to_check.json` (37 records), then `sync_state(dry_run=True)`.
- Output: `{'discovered_papers': 37, 'included_papers': 20}`. Role assignment is by filename tokens (`workspace/counts.py:219-238`).
- Second command: a corrupt `synthesis_matrix.json` and a corrupt `knowledge_graph.json`.
- Output: `matrix_studies: 0, graph_nodes: 0` (`orchestrator.py:352-357, 417-423`). The docstring promises "UNREADABLE (never as 0)" (`orchestrator.py:343-345`).
- Without `--dry-run` these values go into `project.json`, `INDEX.md` and the phase label.

**CORE-17 — Medium — `setup-mcp` writes API keys in plaintext into workspace files that are not gitignored.** Static, plus a `git check-ignore` check.
- `OPENAI_/ANTHROPIC_/GEMINI_API_KEY` and `SCHOLAR_*`/`NEXUS_*` values are copied into `<ws>/.mcp.json` and `<ws>/.cursor/mcp.json` (`mcp_setup.py:33-41, 94-106, 157-165, 294`).
- `git check-ignore -v workspaces/demo/.mcp.json workspaces/demo/.cursor/mcp.json workspaces/demo/.env` matched nothing (rc=1), and AGENTS.md states that workspace text files are tracked.

**CORE-18 — Low — Legacy event IDs collide and are not reproducible.** Reproduced.
- Two identical `append_legacy_event` calls in the same second produced `['EVT-20261103000307-223774', 'EVT-20261103000307-223774']`.
- `hex(hash('A'+'B'))[-6:]` printed `a42950`, then `ac53fe` on the next interpreter run (string-hash randomisation; `workspace/audit.py:258`).
- Coordinator PAUSE rows have fixed descriptions, so re-runs inside one second collide.

**CORE-19 — Low — The CLI summary always reports "Included (PRISMA): 0", and `papers_to_screen` counts the wrong set.** The first is reproduced, the second is static.
- The panel reads `screening.included`/`included_count` (`cli.py:756-759`). The coordinator never sets those keys. The rendered panel shows `Included (PRISMA): 0` next to `awaiting PRISMA screening: 8`.
- `papers_to_screen = len(verified_docs)` (`coordinator.py:454`), but the batches are built from the snapshot's studies (`batcher.py:258-265`), a different set.

**CORE-20 — Low — Placeholder provenance and "success" reported for empty exports.** Static, with the LaTeX/Typst behaviour reproduced.
- Indexing requests carry `producer_commit = "0" * 40  # Would come from harness commit in real usage` (`pipeline/indexing.py:624`). The batcher already has a real `_harness_commit()` (`screening/batcher.py:26-36`) that is not used here.
- `export latex/typst` with no synthesis writes "No synthesis found" (`latex_typst.py:175, 266`), and the CLI prints "✅ Successfully exported" (`cli.py:942`).

## 4. Research-method fitness

Measured against PRISMA 2020, PRISMA-S and the Cochrane Handbook (chapters 4 and 5).

**CORE-21 — Medium — The search is not reportable to PRISMA-S standard from the ledger.** Reproduced with `repro_disc.py`, a fake engine with two providers returning 100 records each.
- The `DISCOVERY_SEARCH` parameters are only `corpus_published, max_results, method, providers, reason, search_tool, stale_artifacts…` (`pipeline/discovery.py:493-503`).
- The query string is not recorded (`query text recorded: False`).
- Per-database record counts are not recorded, only `raw_hits: 200, providers_succeeded: 2`. `_ProviderProbe.succeeded` holds them but is never persisted (`discovery.py:148-152, 505-515`).
- The year and language limits from `compile_protocol_search` are not recorded.
- There is no truncation flag when a provider stops at `max_results`. The kit default is 100 per query (`scholar_search/protocol_adapter.py:74`). A capped harvest is still `SUCCESS` (`discovery.py:216-249`).
- The raw search files are overwritten on every run, with no dated snapshot (CORE-06). `all_raw_search.json` and `raw_search.json` are byte-identical (`discovery.py:405-414`).
- *Consequence.* PRISMA-S items 8 (full search strings), 9 (limits), 13 (dates) and the per-source "records identified" box of the flow diagram cannot be reconstructed from the harness's own records.

**Identity and reproducibility.** CORE-06 means a rerun is not a replay: record IDs, raw counts and screening-batch content can all change. Cochrane expects the search to be re-runnable and the screened set to be fixed and auditable; this pipeline gives neither guarantee unless the user never runs `run` twice.

**Screening integrity.**
- *What works.* The pause gate does what it should (`coordinator.py:458-479`). The AG-03C currentness gate blocks stale generations (`coordinator.py:503-529`).
- *Bypass.* The legacy path (CORE-12) admits an unauthorized `included.json` to extraction and synthesis without stamping the result.
- *Out of scope here.* Whether screening is dual and independent (Cochrane MECIR C39/C40) is decided in `screening/` and `authority/`, which other assessments cover. Nothing in the core pipeline requires or records a second reviewer.

**Verification labels overstate (CORE-09, CORE-10).** "verified" in `verified.json`, in the stage mapping and in the journal means "identity resolved", not "existence confirmed". For a review that will cite these records, the difference matters.

**CORE-22 — Medium — Synthesis and status outputs claim more than the code measures.** Static.
- Stage 9 synthesises only `research_questions[0]` (`pipeline/synthesis.py:107-115`). It writes the result to `synthesis/literature_review.md`, overwriting any earlier one, and logs `PIPELINE_RUN_COMPLETED` for the review as a whole.
- The CLI headline "Grounded Claims: X / Y verified" reports the kit's entailment score, not human verification (`cli.py:774-779`).
- Stage 5 counts abstract-only "metadata frontmatter" documents as `extraction.documents` (`pipeline/extraction.py:171-189`). The panel shows them as "Markdown Extracts" with no full-text/abstract split, although the list is in `metadata_frontmatter_only`. Matrix rows built from abstracts are not marked as such.
- `get_status` declares `PHASE_3_COMPLETE` once the review exceeds 50 characters and any chunks exist (`orchestrator.py:305-311`).
- Extraction, matrix, graph and synthesis emit no audit row of their own (`extraction.py:33`, `matrix.py:30`, `synthesis.py:26-28`). The data-extraction step has no per-stage provenance in the ledger.

**Strengths worth keeping.**
- The discovery outcome taxonomy, which never reports an empty or failed harvest as a success (`discovery.py:216-249`).
- Fail-closed publication of the raw corpus (`discovery.py:394-414`).
- The typed refusal quarantine (`verification.py:155-184`).
- CLI exit codes and headlines derived from status rather than from the absence of an exception (`cli.py:612-640`).

These are the right instincts. The problem is that they stop at Stage 3.

## 5. Doc drift

Only claims shown false above:

- `pipeline_executor.py:15-16` says nodes are skipped when "outputs already exist AND the node fingerprint matches". The code checks existence only (`:247-254`).
- `agent_screen.py:89` says `prepare` will "Chunk verified.json into batch files". The batches are built from the accepted `corpus_snapshot`, and `verified.json` is used only for abstracts (`batcher.py:217-265`).
- The `sync_state` docstring says "an artifact that cannot be read is reported as UNREADABLE (never as 0)" (`orchestrator.py:343-345`). Matrix, graph and merged-record counts become 0 (CORE-16).
- `discovery.py:391` says "Save both combined raw and first-provider raw". Both files contain the same combined payload.
- The hydration row "Hydrated missing abstracts for N documents" uses N = all documents, not the number hydrated (`hydration.py:291`).
- The coordinator comment at `coordinator.py:486-489` says LEGACY_UNVERIFIED is reported "explicitly — never a silent pass". It is reported only to the Python logger (CORE-12).
- AGENTS.md says every significant step is logged *and* reflected in `project.json`/`INDEX.md`. Legacy pipeline rows skip the manifest (`workspace/audit.py:244-246`), and the PipelineSpec executor logs nothing.

## 6. Prioritized recommendations

| ID | Severity | Effort | Action |
|---|---|---|---|
| CORE-06 | Critical | M | Make record identity order-independent (content-derived IDs, or sort before dedup in the harness call), stop re-running discovery on resume, and join batch abstracts by snapshot study ID or stored record, never by SCI alias against a freshly written file. |
| CORE-08 | High | S | Gate stages 7–9 on `index_res["status"] in {SUCCESS, PARTIAL}`. Otherwise mark them SKIPPED and fold the stage statuses into `results["status"]` and `_ledger_status`. |
| CORE-01 / CORE-07 | High | M | Add `run --from screening` (resume) and an explicit corpus-snapshot acceptance step inside the pipeline. Catch `SystemExit` from `cmd_prepare` and write a typed `PIPELINE_RUN_ABORTED` row. |
| CORE-09 | High | S | Persist the kit's per-record `verified`/`status` into `verified.json` and report `existence_verified` separately from `identity_resolved`. |
| CORE-10 | High | S | Refuse a bridge restore when the restored `workspace_id` is already claimed in this batch, or when the verifier's DOI differs from the input record's DOI. Quarantine both records. |
| CORE-21 | Medium | S | Log the compiled query text, limits, per-provider counts, a cap-hit flag and the search date in `DISCOVERY_SEARCH`, and keep dated raw snapshots. |
| CORE-12 | Medium | S | Stamp `LEGACY_UNVERIFIED` into `results` and the COMPLETED row, or refuse unless an explicit `--allow-legacy` is given. |
| CORE-11 | Medium | S | Default `--protocol` to `<workspace>/protocol.json`, and refuse when the search protocol fingerprint differs from the workspace protocol. |
| CORE-14 | Medium | M | Fix the gallery argv (`scholar-search search`, a positional workspace), resolve embedded templates, use real fingerprints for idempotency, exit non-zero on `failed`, and journal each node. |
| CORE-15 | Medium | S | Read DOIs through `_study_doi`, remove the fabricated year default, rename `LIVE_API` and "Synced" to what actually happens, and fix the test fixtures to the real row shape. |
| CORE-16 | Medium | S | Report UNREADABLE for derived artifacts, and restrict PRISMA stat keys to canonical `literature/` files, with non-canonical sources in a separate field. |
| CORE-17 | Medium | S | Write secrets only to user-level config (or reference environment variables), and gitignore `workspaces/**/.mcp.json`, `.cursor/` and `.env`. |
| CORE-13 | Medium | S | Advance one phase at a time, and only when the current phase's triggers are present. |
| CORE-22 | Medium | M | Synthesise per research question or label the output as RQ1-only, separate abstract-only extractions in counts and matrix rows, and emit per-stage audit rows. |
| CORE-03 | Medium | M | Choose one vector-store path and one phase model, and derive the others from it. |
| CORE-02 | Medium | S | Collapse `MinimalIndexer`, delete the dead code, and stop calling defect preservation "fidelity". |
| CORE-18 | Low | S | Use the `append_event` UUID scheme for legacy rows. |
| CORE-19 / CORE-20 | Low | S | Show the included count from `included.json` and the candidate count from the batches. Use `_harness_commit()`. Make empty exports warn rather than report success. |
| CORE-04 / CORE-05 | Low | M | Converge on one journal schema, and consider hash chaining for tamper evidence. |

## 7. Limits of this assessment

- **No live runs.** No provider search, embedding or ChromaDB indexing was run. Every network or ML stage was faked, so kit-side behaviour under real latency is inferred from code. For CORE-06 the end-to-end mis-attachment is reasoned, not observed. Its components (order-dependent IDs, the alias join, the per-run rewrite) were each confirmed separately.
- **Not reviewed in depth:**
  - `extraction_producer.py` (1,795 lines) and `index_acceptance.py` (976): only their entry points and refusal paths were read.
  - `doctor.py`: outline only.
  - `skills_portability/`: not read beyond file sizes.
  - `workspace/identity.py` and `loader.py`: called from the code read, not reviewed on their own.
- **Left to other assessments.** `screening/`, `authority/`, `contracts/`, `console/` and the inception code are covered elsewhere. They were read here only where the pipeline calls into them (`batcher.cmd_prepare`, `require_current_generation`, the gallery templates).
- **Test runs.** Only the six targeted suites listed in the header were run. The full harness suite and the cross-platform CI matrix were not.
- **Repro scripts.** They are in the session scratchpad and were not added to the repo: `repro_pipeline.py`, `repro_cli_proto.py`, `repro_verify.py`, `repro_bridge.py`, `repro_index_fail.py`, `repro_disc.py`. The remaining reproductions were inline `uv run python -c` commands, quoted above.
