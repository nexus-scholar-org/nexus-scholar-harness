# Harness contracts and screening assessment — 2026-11-03

Status: independent assessment, read-only. Commit 5deb3a1. Scope: `src/scholar_harness/contracts/` (4,248 lines), `authority/` (4,438), `capabilities/` (3,048), `claims/` (319), `screening/` (3,993); about 16,000 lines in total, plus the tests that cover them. Method: I read the collector, batcher, integrity, worker, report, decision-contract reader, contract models, canonical, identifiers, acceptance, chain, confirmation, the approval/review/generations/pairing modules and the capability adapters line by line. I skimmed `envelope/`, `lifecycle.py`, `isolation.py` and the egress/view code. I ran `uv run python scripts/generate_contract_baseline.py --check`, which printed "Contract baseline current", exit 0, so the baseline has not drifted. I ran `ruff --select F` on the scope. I ran 488 targeted tests (screening migration, decision integrity, cross-kit contracts, artifact chain, `tests/authority`, confirmation, capability adapter, claim citation) and all passed. I wrote 9 offline reproduction scripts against temporary workspaces built with the repo's own test fixtures (`tests/test_screening_migration.py::_workspace`). I did not modify any repository file except this one.

## 1. Verdict

The Contract v1 core is sound as a model library: typed envelopes, canonical hashing, identifier registry, and a fail-closed acceptance gate with atomic registry writes. The baseline is not drifted. But the main question for a reviewer is whether the screening path produces outputs a systematic review can defend, and today it does not. The collector **silently drops the second screener whenever no adjudication file exists** (CON-10, Critical, reproduced). It **fabricates provenance**: it assigns `method: LLM` to decisions a human made in the console, plus a 1970 timestamp, the placeholder reason "Agent screened.", a confidence of 0.8 and, for a row with no decision field, `INCLUDE` (CON-11). It **turns dual-screening `MAYBE` into an exclusion**. The acceptance gate **accepts a forged decisions artifact if that artifact names two parent batches** (CON-13). The "operator approval" authority depends on a plain JSON file in the workspace that any agent can write, and approving one batch publishes all of them (CON-02, CON-03). The heavy guard machinery (approval binding, generations, pairing codes, capability adapters) is far more elaborate than the trust boundary under it, and about 3,000 lines of capability code are not used by any production path. The 488 passing tests do not exercise any of the defects above.

| Lens | Rating | One-line reason |
|---|---|---|
| Code quality & architecture | Weak | Sound contract core. But four incompatible decision-row schemas, a hand-copied "mirror" of the collector, 1,000-line `cmd_collect` with two divergent publication paths, authority based on writable files, and a large unwired capability layer. |
| Correctness & bugs | Weak | 1 Critical and 6 High defects reproduced on the publication path; one CLI command (`calibration`) crashes on its default path. |
| Research-method fitness | Weak | Single-reviewer coverage gates are good. Dual screening, the PRISMA counts, the "conflict" label, confidence values and the "confirmed by a person" export claim overstate what is measured. No inter-rater statistic exists. |

## 2. Architecture and code quality

**CON-01 — Four mutually incompatible decision-row schemas; the validator rejects the harness's own output. Medium. Reproduced.**
- `batcher._build_agent_instructions` (`screening/batcher.py:124-136`) tells the screening agent to write a bare JSON *array* of checklist rows: `workspace_id`, `inc_xx`/`exc_xx` booleans and `screening_reasoning`, with no `decision` field.
- The collector expects `workspace_id|study_id`, `decision`, `method`, `screener_id`, `decided_at` and `screening_reasoning` (`collector.py:833-927`).
- The decision-contract reader expects an *object* whose rows carry `screening_id`, `decision`, `reason_code`, `confidence` and `one_line_support` (`decision_contract.py:312-318`, `1188-1192`).
- The worker writes `study_id`, `decision: PENDING_REVIEW` and `reasons` (`worker.py:266-285`).
- The console writes a wrapper without `method` (`console/api/screening.py:69-78`, `204-209`).

The reader's docstring says its default patterns "follow the lane the harness itself produces (`batcher.py`)" (`decision_contract.py:326-329`). Reproduction (`classify_decision_file` with the default contract on a prepared workspace):

```
instructed checklist shape -> BAD ('NOT_A_JSON_OBJECT',)
collector legacy shape    -> BAD ('ID_ORDER_NOT_VERIFIABLE', 'ROW_0_MISSING_SCREENING_ID')
```

The batcher's instructed checklist format is also refused by the only approval path (`authority/review.py:689-696`, `REVIEW_CHECKLIST_UNSUPPORTED`). An agent that follows the instructions therefore produces a file that cannot be approved and so can never be published.

**CON-02 — Operator authority rests on agent-writable workspace files. High. Reproduced.**
- `load_operator_context` takes the approver identity from `literature/screening/operator_context.json` (`authority/review.py:145-197`).
- Its only checks are that the source string equals `"publisher-operator-context"` (hard-coded by the caller, `review.py:195-197`) and that the identity is not in `{"", "agent-unknown", "unknown", "epoch"}` (`binding.py:52`, `103-118`).
- The Windows integrity-level isolation that `binding.py:5-8` names as the real enforcement (`provision_publisher_store`, `run_low_integrity` in `isolation.py:145-200`) is **never called from `src/`**. A grep shows callers only in tests.
- `_is_low_integrity_process()` returns False on any non-Windows host and on any query failure (`review.py:200-270`).
- `mint_publication_approval` and `write_publication_approval` are plain importable functions (`generations.py:347-492`), and the test suites use them to self-approve (`tests/test_screening_migration.py:128-170`).

The repo's own decision record says "a freely writable JSON file plus a hash is insufficient … do not claim enforced separation" (`docs/architecture/agent-controls/agent_controls_decision.md:63-70`). Reproduction: I wrote `{"operator_identity":"any-agent-can-write-this"}`, called `approve_command`, then `cmd_collect`, and the outputs were published with that identity in `generation.json`. `binding.py:3-8` honestly calls itself a "narrow feasibility adapter"; downstream consumers (`require_current_generation`, export) nonetheless treat the result as authorization.

**CON-03 — One batch approval authorizes publication of every batch. High. Reproduced.**
`approve_command(ws, k)` validates only batch *k*. It then computes publication content for **all** batches, reading the other batches' decision files from disk unreviewed (`review.py:882-913` → `_compute_single_screener_content`, `review.py:658-672`), and mints one publication approval over the whole set. The per-batch approval files (`batch_approval_path`, `review.py:862-875`) are written but never verified anywhere; `grep batch_approval_path` finds only the writer and console display code. Reproduction on a two-batch workspace: approving batch 2 only gives

```
batch1 approval exists: False | batch2 approval exists: True
published included: 2 operator: any-agent-can-write-this
```

**CON-04 — The approval path re-implements the collector by hand. Medium. Static.**
`_compute_single_screener_content` (`review.py:558-760`) is described as a "bounded mirror" of `cmd_collect`. Its semantics already differ:
- It refuses rows with a missing or non-terminal `decision` (`review.py:699-705`); the collector defaults them to `INCLUDE` (`collector.py:851`).
- It refuses checklist rows; the collector derives decisions from them (`collector.py:838-849`).
- It refuses dual-screening inputs (`review.py:601-608`); the collector has a dual path.

Only a byte-identity test keeps the two aligned. Any change to the collector's serialization or partition makes every approval fail with `APPROVAL_CONTENT_CHANGED`, while a change in which rows are accepted can let the two paths silently disagree about what was reviewed. The fix is to have one function that produces the publication content and have both callers use it.

**CON-05 — `cmd_collect` is a ~1,000-line function with two publication paths of unequal rigor. Medium. Static.**
- The single-screener path runs the AG-02 gates: stale binding, replay, `CONTENT_CHANGED`, exact coverage, duplicate entries, refusal of unresolved rows, and decision-file hash lineage (`collector.py:719-796`).
- The dual path (`collector.py:338-677`) runs **none** of them. It checks only one-way membership (decision ⊆ candidates, `385-420`), does not refuse duplicates (`s1_map[...] = r` silently keeps the last of repeated rows, `434`, `449`), records no `decision_file_sha256` lineage and writes no MANIFEST lineage.
- Both paths swallow broad exceptions: an unparseable screener-1 or screener-2 file is skipped (`430-431`, `445-446`), an unparseable adjudication file is ignored (`458-459`), and so is the provenance manifest (`1112-1113`).
- The two paths stamp different producer packages (`"nexus-scholar-harness"` at `645` versus `"scholar-harness"` at `986`) and use different artifact-id recipes (`628-635` versus `967-977`; see CON-15).

**CON-06 — The capability layer and the chain validator are not used by any production path; "enforced" is cooperative. Medium. Static.**
- `capabilities/` (3,048 lines) is imported only by `tests/conformance/test_capability_adapter.py` and `test_skill_portability.py`.
- `validate_artifact_chain` (`contracts/chain.py:91`) and `claims/` are imported only by tests and generator scripts.
- `InProcessAdapter` advertises "enforced capability … path validation at every I/O" (`inprocess.py:1-6`). The handler, however, is an arbitrary in-process callable: nothing prevents `open()` outside `RoleSession`. The egress guard monkeypatches `socket` attributes and documents its own bypasses (`adapter.py:1521-1537`).
- `OpencodeAdapter` says it runs "with pre/post path checks; violations are logged" (`opencode.py:18`, `69`, `131`). `run()` (`opencode.py:128-240`) performs no filesystem pre/post comparison at all; a grep for any scan or walk finds none.

**CON-07 — Duplicated contract rules, with the same hole in both copies. Low. Static.** `_ARTIFACT_MODELS` and `_REQUIRED_PARENT_TYPE` are defined twice (`acceptance.py:31-45`, `chain.py:23-32`). The batch-binding checks are also written twice, and both copies skip the check when there is not exactly one parent batch (`acceptance.py:433`, `chain.py:250`); see CON-13.

**CON-08 — The pairing code is cryptography over agent-writable state, and it is optional. Low. Reproduced (crash).** The pairing challenge uses 130-bit CSPRNG codes, PBKDF2 hashing, attempt caps and expiry (`pairing.py:70-75`, `285-317`). Its state (`attempts_used`, `consumed`, `expires_at`) lives in a workspace JSON file (`pairing.py:386-402`), and `approve` without `--begin` skips pairing entirely (`review.py:937-998`). The protection is therefore much stronger than the boundary it sits on. A side effect: `verify_code("ÄBC", hash_code("ABC"))` raises `UnicodeEncodeError` (`pairing.py:315`, `normalize_code(...).encode("ascii")`) instead of counting a failed attempt.

**Minor hygiene (ruff F).** There are unused imports or variables at `report.py:12,14`, `adapter.py:81`, `inprocess.py:27`, `confirmation/api.py:32`, `isolation.py:174` and `review.py:654`. The two undefined names are a real bug (CON-17).

**Strengths that matter for decisions:**
- `accept_artifact` (`acceptance.py:232-622`) is a sound design: it validates the schema, checks expected fingerprints, verifies the hash of each registered parent and the registry entry against its payload, uses atomic writes with registry rollback, and keeps a bounded rejection ledger.
- Canonical JSON (`canonical.py:42-125`) rejects NaN and infinity and requires set-like arrays to be declared explicitly.
- The single-screener AG-02 gates (`integrity.py:65-127`) are correct and well targeted.
- Generation publication renames `generation.json` last and refuses on lock contention (`generations.py:803-938`).

## 3. Correctness and bugs

**CON-10 — Dual screening silently becomes single screening when no adjudication file exists. Critical. Reproduced.**
- What happens: dual mode starts only when *both* `batch_*_decisions_screener2.json` **and** `_adjudication_resolved_group_*.json` exist (`collector.py:338`). Otherwise the single path runs and never reads screener 2.
- When it triggers: all-agreement runs (no adjudication needed) and runs where disagreements are still unadjudicated. The existing test has to plant an empty `"[]"` adjudication file to reach dual mode at all (`tests/test_screening_migration.py:290-292`).
- Evidence: screener 1 INCLUDE, screener 2 EXCLUDE, no adjudication file:

```
[A dual: s1 INCLUDE, s2 EXCLUDE, no adjudication file] included=1 excluded=0 n_contract_decisions=1
  first={'screener_id': 'r1', 'method': 'HUMAN', 'decision': 'INCLUDE', ...}
```

- Impact: the disagreement disappears, screener 1 wins, and the Contract v1 artifact records a single decision. The output is reported as a normal screening and nothing flags it. This breaks the frozen rule "Dual screening requires two provenance-complete parent decisions" (`DEVELOPER_COMPASS.md:111-113`).

**CON-11 — The collector fabricates provenance and default decisions. High. Reproduced.**
- What happens: in the single path, an absent `method` becomes `LLM` (`collector.py:925`). An absent `screener_id` becomes the wrapper's `reviewed_by`, or `"agent-unknown"` / `"agent-legacy"` (`collector.py:922-924`, `batcher.py:174`, `180`). An absent timestamp becomes `1970-01-01T00:00:00+00:00` (`batcher.py:179`, `collector.py:919-921`). An absent reason becomes `"Agent screened."` (`collector.py:886-888`, `928`). An absent or invalid confidence becomes `0.80` (`collector.py:870-873`). An absent decision becomes `"INCLUDE"` (`collector.py:851`).
- Why it matters in practice: the console never writes `method` (`console/api/screening.py:69-78`), so **every decision a human makes in the console is recorded in the Contract v1 artifact as `method: LLM`, `screener_id: "console"`**.
- Evidence:

```
[B row with no decision key, no method, bare list] ... {'screener_id': 'agent-legacy', 'method': 'LLM',
   'decision': 'INCLUDE', 'reason': 'x', 'decided_at': '1970-01-01T00:00:00Z'}  confidence 0.8
[C row {} in wrapper] ... {'screener_id': 'r1', 'method': 'LLM', 'decision': 'INCLUDE', 'reason': 'Agent screened.'}
```

- Scope: the default to `INCLUDE` is blocked when the approval is minted through `approve_command` (its mirror refuses a missing decision). It is not blocked in the collector itself, and approvals can be minted directly (CON-02). The `LLM` mislabel passes through the official path.
- Rules contradicted: "Record the actual method … Do not invent timestamps, screeners" (`DEVELOPER_COMPASS.md:101-105`) and "Silent LLM-to-heuristic substitution is not permitted" (`cross_kit_contract_v1.md`, Screening).

**CON-12 — The checklist path discards the screener's rationale and invents confidence. High. Reproduced.**
- What happens: the collector calls `checklist_to_decision` without passing `screening_reasoning` (`collector.py:842-849`; the kit signature accepts it, `tools/scholar-agent-kit/src/scholar_agent/calibration.py:65-74`). The rationale the batch instructions require is lost.
- Evidence: the published `included.json` carries `'screening_reasoning': ''`, and the Contract decision carries `"Agent screened."`.
- Confidence: the values are the constants 0.90, 0.75 and 0.55 chosen by rule (`calibration.py:108-116`). They are not a measured confidence.
- Missing fields: a checklist field absent from the row is read as `False` (`calibration.py:97`). A partially filled checklist therefore becomes an EXCLUDE with no error.
- Protocol drift: the checklist schema is built from the *current* `protocol.json` (`collector.py:841`), not from the protocol fingerprint the batch was bound to (see CON-16).

**CON-13 — The acceptance gate can be bypassed by declaring two parent batches. High. Reproduced.**
- What happens: the batch-id, binding and decision-membership checks run only when `len(matching_parents) == 1` (`acceptance.py:433`). The "at least one parent of the required type" check passes with two.
- Evidence: a forged `screening_decisions` artifact with a tampered binding (`criteria_renderer_version: "TAMPERED"`), a nonexistent `batch_id` and a study absent from both batches:

```
ONE parent  -> accepted: False ['SCREENING_BATCH_ID_MISMATCH', 'SCREENING_BINDING_MISMATCH', 'DECISION_OUTSIDE_BATCH']
TWO parents -> accepted: True []
```

- Impact: the registry accepts an artifact the frozen contract says must be refused ("Mismatch is a closed gate"). The reference validator has the same skip (`chain.py:250`).

**CON-14 — Dual mode coerces unresolved decisions into exclusions. High. Reproduced.**
- What happens: the dual path builds a "consensus" whenever the two decisions are equal, including `MAYBE`/`MAYBE` and `CONFLICT`/`CONFLICT` (`collector.py:517-559`), and it never calls `check_no_unresolved_for_finalize`. The kit partition then files every non-INCLUDE row under `excluded` (`scholar_search/screening.py:479-484`).
- Evidence: `MAYBE/MAYBE dual -> included 0 excluded 1 decision in excluded: MAYBE`.
- Impact: the PRISMA "Records Excluded" count includes unresolved records. The single path explicitly refuses this (`integrity.py:103-127`), and AG decision §5 forbids it.

**CON-15 — In dual mode, a corrected decision can never be re-collected. Medium. Reproduced.** The dual artifact id is derived from `batch_id` only (`collector.py:628-635`). Any corrected screener file produces a different payload under the same id, which gives `IDEMPOTENCY_CONFLICT`, and collection fails permanently for that batch: `re-collect after correction -> RuntimeError ... IDEMPOTENCY_CONFLICT`. The single path includes the decision ids in the hash (`967-977`) and does not have this problem.

**CON-16 — Collect does not re-check the protocol against the batch binding. Medium. Reproduced.** Only `prepare` compares `protocol.json` with the corpus (`batcher.py:231-236`). `collect` takes its "expected" fingerprints *from the parent batch envelope itself* (`collector.py:1014-1018`), so the check refers back to itself. After I edited the exclusion criteria post-prepare, collect published (`included.json exists = True`) and only the downstream `require_current_generation` reported `GENERATION_MISMATCHED`. The gate is in the wrong place: a stale generation is committed to `generation.json` first and rejected only later.

**CON-17 — `agent_screen.py calibration` crashes on its default path. Medium. Reproduced.** `report.py:51-52` calls `_rebuild_doc` and `evaluate_heuristic_screening`, neither of which is imported (ruff F821). Running `cmd_calibration` without `--gold` gives `NameError name '_rebuild_doc' is not defined`. The default `main()` help text presents calibration as step 1 of the workflow (`agent_screen.py:62`).

**CON-18 — Status and MANIFEST misreport batches. Low. Reproduced (status).**
- `cmd_status` iterates the parsed JSON as a list (`collector.py:80-86`), so the console's own wrapper format always shows `DONE (parse error)`.
- MANIFEST status is `DONE` whenever the decisions file exists (`collector.py:1075-1078`), including a batch whose file failed to parse at `697-700` and was not renamed.

**CON-19 — Registry read-modify-write without a lock. Low. Static.** `accept_artifact` reads the registry, adds an entry and replaces the file (`acceptance.py:331`, `552-573`) with no inter-process lock. Two concurrent acceptances (console plus CLI) can lose one registry entry while its artifact file remains on disk, after which retries fail with `ORPHAN_ARTIFACT_PATH` (`acceptance.py:537-551`).

## 4. Research-method fitness

**What is defensible.** For a single reviewer (the user's actual setup), the human path has good integrity properties:
- Exact 1:1 coverage of the accepted batch, refusal of duplicates and refusal to finalize `MAYBE`/`CONFLICT` (`integrity.py`).
- Membership checked against the *accepted* batch rather than the mutable handoff file (`collector.py:798-825`).
- Content-addressed decision-file lineage.
- Publication bound to byte digests, with a downstream currentness check.

Keep these when fixing everything else.

**CON-20 — PRISMA counts conflate exclusion reasons and fabricate zero. Medium. Static.**
- `duplicates_removed = total_raw_harvested − len(verified.json)` (`collector.py:1104-1111`; the same in `review.py:730-737`). Every record removed between harvest and `verified.json` is reported as a duplicate. That includes Stage-3 identity quarantine (`collector.py:275-285`) and verification drops. PRISMA 2020 requires duplicates and other pre-screening removals to be reported separately.
- When `provenance_manifest.json` is absent or unreadable (with `except Exception: pass` at `1112`), the report states "Total Records Identified (Federated Search): N" equal to the screened count, and "Duplicates Removed: 0", with no indication that these numbers are unknown.
- The exclusion-reason table counts each violated criterion, so one record can be counted several times and the rows do not sum to "Records Excluded" (`scholar_search/screening.py:483-484`). Legacy rows rarely carry criteria, so most exclusions appear as `UNSPECIFIED`.

**CON-21 — "Conflicts" and "confidence" are not measurements. Medium. Static.**
- `conflicts.json` and "Borderline Conflicts Flagged for Human Audit" mean confidence in the range 0.40–0.70 (`scholar_search/screening.py:475-477`). Confidence is either a constant (0.8 by default, CON-11) or a rule constant (0.55 for *any* exclusion-criterion hit, CON-12). As a result, every checklist exclusion with a triggered exclusion criterion is labelled a "conflict", while genuine dual-screener disagreements are never counted as conflicts.
- In dual mode the published confidence comes from screener 2 or the adjudicator, with a default of 0.8 (`collector.py:567-568`). Screener 1's criteria are discarded on agreement (`569-571`).
- These labels should be renamed (for example, "rule-flagged for audit") or computed from real disagreement.

**CON-22 — No inter-rater reliability, no disagreement accounting, no enforced independence. Medium. Static.**
- Nothing in `screening/` computes agreement, Cohen's κ or a prevalence-adjusted equivalent (grep: none). A Fleiss κ helper exists elsewhere (`tests/integrations/test_rigor_upgrades.py:60`) but is not wired in.
- The PRISMA report has no field for the number of dually screened records, disagreements or adjudications.
- Independence between screeners is not enforced: screener 2 is simply a file that sits next to screener 1's file, and the blinding views exist only in the unused capability layer (CON-06).
- A review that states "two independent reviewers, disagreements resolved by adjudication" cannot show any of this from the harness outputs.

**CON-23 — LLM-as-screener validity is unsupported. Medium. Static.**
- The contract makes `model_id` and `prompt_version` optional even when `method == LLM` (`contracts/models.py:591-592`).
- The batch prompt has no version or hash in the binding (`criteria_renderer_version` is taken from `protocol.metadata.version`, `batcher.py:271`).
- The only validation tool (calibration) crashes (CON-17). Even if fixed, it would build its "gold" labels from the keyword heuristic when no gold file is supplied (`report.py:43-63`) and then report an LLM screener as "PASSED" against heuristic labels. That is agreement with a heuristic, not accuracy, and calling it "gold" overstates it.

**CON-24 — "Confirmed by a person" export accepts a confirmation that reviewed nothing. High. Reproduced.**
- What happens: `HumanConfirmation@1` requires `decisions: list` with no minimum, and `summary.considered` only has to equal the length of that list (`confirmation/model.py:123`, `api.py:186-205`). It hashes the decision *input* files but not the published `included.json`/`excluded.json`/`generation.json`, nor `verified.json` or `protocol.json`, which also determine the outputs (`api.py:264-273`). The reviewer name is free text.
- Evidence: a record with zero decision rows over a 500-row decisions file:

```
export_gate ACCEPTED: reviewer=Anyone, rows_reviewed=0, screened_rows_in_artifact=500
```

- Impact: `scholar-harness export --claim-confirmed` then prints "Human confirmation: signed by …" (`cli.py:915-932`). That overstates human review of the screening.

**Criteria traceability (Low).** `matched_inclusion_criteria` and `violated_exclusion_criteria` are copied from the rows without checking them against the protocol's criterion ids (`collector.py:879-884`), so a typo or a stale id passes through into the reasons table.

## 5. Doc drift (claims proven false)

- `DEVELOPER_COMPASS.md:101-113`, §6 ("needs, at minimum: decision_id, screener_id, method, decided_at…; missing lineage blocks collection"; "Dual screening requires two provenance-complete parent decisions"): false for the single path, which accepts `{}` (CON-11), and for dual screening without an adjudication file (CON-10).
- `agent_controls_decision.md:66-74` ("Agent interfaces cannot mint approvals"; "never coerce [MAYBE/CONFLICT] to EXCLUDE"): approvals come from a writable file and importable functions (CON-02), and the dual path coerces MAYBE (CON-14).
- `cross_kit_contract_v1.md` Screening ("Mismatch is a closed gate"): bypassed by two parent batches (CON-13) and by protocol edits after prepare (CON-16).
- `capabilities/opencode.py:18,69,131` ("pre/post path checks log violations"): no such checks exist (CON-06).
- `screening/decision_contract.py:326-329` (default patterns "follow the lane the harness itself produces"): the harness's own output is classified BAD (CON-01).
- `AGENTS.md`, `batcher.py:416-417` and `collector.py:101` all say the agent writes decisions and then `collect` assembles the outputs. That is incomplete: without a staged approval, `collect` refuses with `APPROVAL_MISSING` (`collector.py:1123-1136`).

## 6. Prioritized recommendations

| ID | Severity | Effort | Action |
|---|---|---|---|
| CON-10 | Critical | S | Enter dual mode whenever any `*_screener2.json` exists. Refuse when there is a disagreement without adjudication; never fall back to the single path. |
| CON-11 | High | S | Remove every provenance default (`method`, `screener_id`, `decided_at`, `reason`, `decision`, `confidence`) and refuse instead. Make the console write `method: HUMAN` and a real reviewer identity. |
| CON-13 | High | S | In `acceptance.py` and `chain.py`, refuse a `screening_decisions` artifact with anything other than exactly one `screening_batch` parent. Add negative tests. |
| CON-14 | High | S | Run `check_no_unresolved_for_finalize` on the final dual decisions. Add the AG-02 coverage, duplicate and lineage gates to the dual path (CON-05). |
| CON-02/03 | High | M | Either provision and require the integrity-level separation, or relabel approval as "recorded operator attestation (unauthenticated)" everywhere. Require a verified per-batch approval for every batch in the publication scope. |
| CON-24 | High | S | Require the confirmation to cover every published study (or state its coverage), and bind it to `generation.json` and output digests. Print coverage in the export narration. |
| CON-12 | High | S | Pass `screening_reasoning` through. Refuse missing checklist fields. Derive the checklist schema from the bound protocol fingerprint. |
| CON-16 | Medium | S | Re-fingerprint `protocol.json` at collect and refuse a mismatch before any acceptance. |
| CON-01/04 | Medium | M | Define one decision-row schema used by the instructions, console, worker, reader and collector. Replace the review "mirror" with the collector's own content function. |
| CON-20–23 | Medium | M | Split PRISMA removal reasons, mark unknown counts as unknown, rename "conflicts", report agreement statistics (κ with prevalence context) and disagreement/adjudication counts, and require `model_id`/`prompt_version` for LLM decisions. |
| CON-15 | Medium | S | Include decision ids in the dual artifact id. |
| CON-17 | Medium | S | Fix the imports. Refuse calibration without a human gold file, or label it "heuristic agreement". |
| CON-06 | Medium | M | Either wire the capability layer or mark it experimental. Remove the false "pre/post checks" and "enforced" claims. |
| CON-18/19/08 | Low | S | Fix status parsing and MANIFEST status, add a registry lock, catch non-ASCII codes. |

## 7. Limits of this assessment

- I did not read `contracts/envelope/api.py` or `registry.py`, `lifecycle.py`, `generations.require_current_generation`/`recover_partial` (`generations.py:1145-1490`), or the view-materialisation code in `adapter.py` in full. Defects may remain there.
- I did not run the full harness test suite, the cross-platform matrix, or the schema and fixture generators (`generate_contract_schemas.py --check`, `generate_two_study_contract_fixture.py --check`). Only the baseline check was run.
- I did not run the Windows integrity-level isolation tests or the console HTTP routes end to end. Statements about the console come from reading `console/api/screening.py:60-239` only.
- I did not trace whether real workspaces contain dual-screening data affected by CON-10/CON-14. The workspaces were emptied (AGENTS.md), so I could not check historical outputs.
- Kit-side behaviour (`scholar_search.screening.partition_screening_results`, `scholar_agent.calibration`) was read only as far as the harness depends on it. Those kits are covered by other assessments.
- Reproductions used temporary workspaces built from the repo's test fixture (one or two synthetic studies). They demonstrate the mechanisms, not their prevalence in real data.
