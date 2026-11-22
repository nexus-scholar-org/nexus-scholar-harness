# M11b Criteria pilot

Branch: `dev/m11b/criteria-pilot-spec` (from `origin/main` at `1f218054`) · Lane: declared per part (proposed below: A, B and D **RELEASE**, C **STANDARD**) · Status: **SPECIFICATION; the researcher answered the ten questions on 2026-11-21** (1 to 4, 7, 9 and 10 as recommended; **5, 6 and 8 against the recommendation**). Questions 11 and 12, which came from those answers, were answered the same day, both as recommended. The rework of answers 5, 6 and 8 is PROPOSED. **Build started 2026-11-21 (approved by the researcher; building, not pushing): part A READY FOR PR again on `dev/m11b/part-a-criteria-in-force` (item 5 built as decided; item 11 PROPOSED) (see "Build record"); part B READY FOR PR on `dev/m11b/part-b-pilot` (since merged, PR 277); part C READY FOR PR on `dev/m11b/part-c-screens` (items 1 to 17 accepted 2026-11-22); part D in review on `dev/m11b/part-d-step5`** · Fourth in the agreed order (plan §6, "After the acceptance run"); M11a part C is merged (PR 272), so part D is no longer blocked by it

Short page for the researcher: [`M11b-criteria-pilot-for-review.md`](M11b-criteria-pilot-for-review.md). Screens (both `Status: DRAFT`): [`docs/ux/phase2-screening/final/13-criteria-pilot.md`](../../ux/phase2-screening/final/13-criteria-pilot.md) (draw the pilot, its result, revise a criterion) and [`docs/ux/phase0-inception/final/11-criteria-block.md`](../../ux/phase0-inception/final/11-criteria-block.md) (the change to Inception's step 5). Choices: `docs/decisions.md`, "2026-11-21 — M11b criteria pilot: the specification's choices" (answered 2026-11-21; the rework of 5, 6 and 8 and questions 11 and 12 PROPOSED).

## The researcher's answers (2026-11-21)

Given in the main session and relayed to this branch. The option the researcher picked is quoted as it read.

| # | Question | Answer | As recommended? | Where this record follows it |
| :-- | :-- | :-- | :-- | :-- |
| 1 | How a revised criterion is recorded | "Amendment beside the protocol" | yes | (a), A1 |
| 2 | Decisions already made | "Kept; affected ones return" | yes | (a); since answer 5 it applies to the main screening's decisions only |
| 3 | Criterion numbers | "Reworded keeps it; others retire"; a number is never reused | yes | (b) |
| 4 | Until when criteria can be revised | "Until the first batch is approved" | yes | (a), "When a revision is allowed" |
| 5 | The pilot sample | **"Pilot decisions not counted"**: "Pilot records are screened again in the main screening. Cleaner separation, double work on those records." Size (50, 20 to 100), the random draw and the recorded seed were not questioned and stay as proposed | **no** | (d) reworked; (a), (e), (h), (i) follow; answer 11 |
| 6 | The checklist during the pilot | **"Closed as today"**: "The result then leans on the agent's answers only." | **no** | (d), (e) and (f) reworked: which readings remain |
| 7 | Warnings without a model | "Rules only" | yes | (f) |
| 8 | Defaults of the two method questions at step 5 | **"No default; I must choose"**: no not-reported rule is pre-selected, and step 5 cannot be passed until one is picked. Draft visibility was not asked separately: "after you decide the record" stays pre-selected, **as a proposal** | **no** | (g) reworked; answer 12 |
| 9 | "Check the agent on these 50 records" | "Yes" | yes | (i); since answer 5 the check compares the agent with the pilot decisions, which are not decision events |
| 11 | The agent's draft for one record in the pilot result | "Counts only": the agent per criterion, never per record; the main screening shows nothing of the pilot decision; the screening contract is unchanged | yes | (d), (e), (i), DoD 11d and 13 |
| 12 | Does the terminal wizard ask too? | "Yes, it asks too": `scholar-harness inception` asks the not-reported rule with no default; a scripted run needs `--not-reported <rule>` | yes | (g), DoD 18c, part D |
| 10 | Build order | "A, B, C, then D" | yes | "Parts": the order still holds. M11a part C is not merged yet (about to be pushed); part D waits for it |

Sources: `docs/roadmap/what-a-researcher-does.md` (step 3: "The criteria change after a pilot: 50 to 100 records are screened, the criteria turn out ambiguous, they are rewritten, and only then fixed"); `docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md` (findings 1, 2, 31, 36 and the section "Screening and agent drafts"); plan §6, row 4; `docs/decisions.md` entries "2026-11-20 — H-screening-drafts" (item 2: the method amendment beside the signed protocol; item 9: Inception does not ask) and "2026-11-19 — M10c" (items 9(a), 16, 21: what a moved fingerprint does); the Inception redesign decisions D1 to D15 (local branch `dev/ux/inception-redesign`, `04-recommendation.md`); `docs/architecture/DEVELOPER_COMPASS.md` §3; and the code at `1f218054`, checked by two `phase-auditor` runs (see "What exists, checked against the code").

## Goal

Let the researcher screen a small random sample of the accepted corpus under their criteria before the full screening, as a pilot whose decisions are kept apart and not counted, and show them where the criteria worked and where they did not. Let them revise a criterion with a recorded reason, as an amendment beside the signed protocol, so the decisions already made stay bound and the counted records a revision could change are shown again. Warn about criteria that mirror or contradict each other before any record is read, and have the researcher choose the two method settings where the criteria are accepted rather than after screening has started.

## What a researcher does at this stage, and what the app offers today

**What a researcher does.** The protocol's criteria are written before any record is read, and they are wrong in ways that only reading shows: a criterion nobody can judge from an abstract, two criteria that say the same thing, a wording the second reader (a supervisor, or now an agent) reads differently. So 50 to 100 records are screened as a pilot, the criteria are rewritten, and only then fixed. The pilot and the revision are reported ("criteria were piloted on 50 records and refined"), and PRISMA-ScR expects deviations from the protocol to be stated.

**What happened on 2026-11-20.** The review had four inclusion and five exclusion criteria and 1,062 records. The wizard turned the proof answer into a criterion that is not a screening rule (finding 1) and lumped the out-of-scope answer into one exclusion (finding 2); five exclusions were typed by hand, several mirroring an inclusion ("RGB only" against "multispectral from a UAV"), and "uses a learned model" sat beside "or a dataset paper", so a dataset paper could not satisfy both. Nothing warned about either (finding 36). Blinding and the not-reported rule were fixed at genesis without a question; the researcher found out on Prepare that "Show beside the record" did nothing (finding 31). Agent drafts came back 83 to 85% Unclear; the rule was the main cause and the mirrored criteria doubled the chances of a `not_reported` answer. The fix for the rule (H-screening-drafts) is an amendment of the method beside the signed protocol. No such path exists for the criteria: changing one means a new workspace.

### What exists, checked against the code

Two `phase-auditor` runs at `1f218054` (read only, no network). Every line below was read in the code; "inferred" marks the two that were not run. E19 to E22 were read by hand on 2026-11-21 for the rework after the researcher's answers (the same code; `origin/main` has since gained M8b, which touches Triage only).

| # | Fact | Evidence |
| :-- | :-- | :-- |
| E1 | Inception step 5 proposes criteria from the proof answer (only when no inclusion is typed), one exclusion per out-of-scope item, typed criteria, and a paradigm default when there is no exclusion. Wizard and out-of-scope items start undecided, typed ones accepted; genesis refuses undecided criteria and a missing side. Wording is never edited in place: a typed criterion is removed and added again | `inception/intent.py:318-352` (`draft_criteria`); `inception/steps.py:507` (`criteria_with_decisions`), `:~620`; UI `components/inception-criteria.tsx:153,158,170,239,279-305` |
| E2 | Inception never asks blinding or the not-reported rule. The draft has no such field; genesis writes a `method` block with the model defaults `blinding: reveal_after_decision`, `not_reported: unclear` | `inception/steps.py:200-247`; `inception/genesis.py:165-175`; `scholar_protocol/models.py:342,351` |
| E3 | The compiler numbers criteria `INC-nn` and `EXC-nn` in the order of the accepted list, so a criterion dropped before genesis renumbers the rest (inferred from the loop). An id is a plain string; uniqueness is checked (`DUPLICATE_CRITERION_ID`); no pattern | `scholar_protocol/compiler.py:79-102`; `models.py:157`; `validate.py:14,28` |
| E4 | The protocol fingerprint is the sha256 of the canonical whole protocol, so it covers every criterion's id and text and the `method` block. It is not stored in `protocol.json`; it is recomputed and stored on what binds to it | `scholar_protocol/canonical.py:60,80-94,112,148` |
| E5 | Bound to the fingerprint: the accepted corpus snapshot (envelope), every batch (envelope and binding), every decision event (`binding{protocol_fingerprint, batch_id, batch_sha256}`; intake refuses `STALE_BINDING`; events under another fingerprint silently stop counting), agent drafts (inside `proposal_id`), method amendments. Prepare exits if the protocol no longer matches the corpus | `corpus_accept.py:1213`; `screening/batcher.py:232-237,282,338`; `screening/events.py:377-406`; `screening/proposals.py:93-95,176-194` |
| E6 | Changing any criterion today moves the fingerprint, and then every decision counts nowhere and Prepare refuses; Next step offers `PROTOCOL_CHANGED_AFTER_BATCHES` (open Inception, archive and start clean). The only post-genesis protocol write, M10c 9(a), amends search fields only and is refused once a corpus is accepted | `console/next_step.py:365-366`; `workspace_proposals.py` (guard `outside_search`, `CORPUS_ALREADY_ACCEPTED`); decision 2026-11-19 M10c item 21 |
| E7 | Method amendments: `POST /screening/method/amendments {field, value, confirm, note}`; one row in `audit/method_amendments.jsonl` (`amendment_id` "AMD-"+24 hex, `field`, `from`, `to`, `protocol_fingerprint`, `amended_by`, `amended_at`, `note`) and a `PROTOCOL_METHOD_AMENDED` journal row; values in force = signed + rows under the current fingerprint (`effective_method`); reported in the methods paragraph | `screening/method.py:92-107,133-141,172-204,237-272`; `console/api/screening_v1.py:507-529`; `screening/export.py:674-706` |
| E8 | A decision event: `event_id`, `screener_id`, `decided_at`, `method: HUMAN`, `outcome` INCLUDE / EXCLUDE / MAYBE, `study_id`, `reason_code` (EXCLUDE only, required, exactly one: an exclusion id or `FAILS-<inclusion id>`, else `REASON_CODE_INVALID`), optional `criteria[{id, answer}]` (the researcher's checklist), `note`, `supersedes`, the binding; the engine stamps `received_at`, `token_scope`, `changed_after_reveal`. Append-only, one file per screener; batch decision files are projections. No round, stage or phase field | `screening/events.py:43-68,119-124,334-386,618,780` |
| E9 | The checklist in Triage is optional and collapsed by default; absent answers stay absent | `docs/ux/phase2-screening/final/03-triage-desktop.md` items 2 and 4 |
| E10 | Batches: the snapshot's study order cut into slices of 20 (5 to 100 from the console); no sort and no seed; each batch file embeds the criteria text in its instructions and is hashed into every decision's binding; the console cannot re-prepare | `screening/batcher.py:76-132,191,208-212,262-271,303-308`; `console/api/screening_v1.py:742-745`; `console/runtimes/actions.py:68` |
| E11 | Agent drafts store one answer per criterion id (`yes`, `no`, `not_reported`, with evidence), the outcome first derived and the rule it was derived under; the shown outcome is re-derived when read under the rule in force. The agent run and the draft reader take the criteria from `protocol.json` | `screening/proposals.py:50,63,144,176,203`; `screening/agent_runs.py:603-614` |
| E12 | The agreement read counts the researcher's decisions made before the reveal against the latest draft: a 2×2 table, `unclear_either_side`, and `splits_by_criterion` (a count per criterion, no denominator) | `console/api/screening_v1.py:1184-1236`; `components/screening-agreement.tsx` |
| E13 | "Check the agent on your labels" exists: `POST /proposals/calibrations {study_ids, provider, model, effort, cost_ceiling_usd}` runs the agent on records already decided (`kind: calibration`). Its body defaults to `claude-opus-5-5`. On the command line, `prompt-gate measure --scope all` measures on the workspace's own decisions (no per-criterion output) | `console/api/screening_v1.py:1144-1166`; `screening/agent_runs.py:575,593`; `scholar_agent/measure.py:113-131,413-474` |
| E14 | The methods paragraph states the not-reported rule, "set in the signed protocol, except as amended below" and one sentence per method amendment; it names no criterion, pilot or calibration | `screening/export.py:445,457,514,674-706` |
| E15 | Inception's criteria checks: `CRITERIA_UNDECIDED`, `CRITERIA_SIDE_MISSING` (blockers), `CRITERIA_REASONS_UNIFORM` (warning). Nothing compares wordings (mirror, duplicate, lumped, needs the full text) | `inception/checks.py:549,695-727`; `docs/ux/shared/final/02-checks.md` |
| E16 | Contract v1 locks `src/scholar_harness/contracts/**`, the ten schemas under `contracts/schemas/v1/` (among them corpus-snapshot, screening-batch, screening-decisions, artifact-envelope), their fixtures and tests, and the listed docs. The protocol schema, `models.py` and `canonical.py` are not in that list (inferred from the globs; the drift check was not run, docs only). The locked `ScreeningDecision` has a free-text `reason` and no reason-code field; `reason_code` lives in the harness event log | `scripts/generate_contract_baseline.py:14-45`; `contracts/schemas/v1/screening-decisions.schema.json:81-92,150-154,177-183,251-276` |
| E17 | A citation-chasing round archives the whole `literature/screening/` folder (`round_NNN`); a round is a folder, not a field on events | `screening/rounds.py:68-73,110,193` |
| E18 | No pilot, sample or criteria revision exists in `src/scholar_harness` (the legacy `report.py` `cmd_calibration` is a 20-paper heuristic pre-flight, not tied to human decisions) | auditor grep; `screening/report.py:25` |
| E19 | *Read on 2026-11-21 for the rework.* The screening API contract (ACCEPTED 2026-11-04, a harness contract, not Contract v1) says: a second non-superseding event for the same study and screener whose outcome differs is a `conflict`, and the study is left out of the projection, so collect refuses it (`BATCH_INCOMPLETE`); `proposal_shown` "is `null` when the researcher decided before any proposal was revealed. With blinding on (the default) it is always `null` at decision time"; "A reveal (M1b-0) is the first time `GET /records/{id}/proposal` returns a proposal to a screener". The methods paragraph's blinding sentences read these | `docs/architecture/screening-api-contract.md` §3.1, §3.3, §3.4; `console/api/screening_v1.py:306-322`; `screening/export.py:813-870` |
| E20 | *Read on 2026-11-21.* `POST /proposals/calibrations` refuses a study that has no decision in the event log ("calibration uses records you have already decided", `INVALID_OUTPUT`, 422) | `console/api/screening_v1.py:1154-1160` |
| E21 | *Read on 2026-11-21.* The intent packet has no `method` field; `compile_intent` fills the model defaults whenever the compiled protocol has no method block. The search amendment of M10c 9(a), which M11a's "Change the search" also uses, recompiles the intent and refuses any change outside the search fields (`outside_search`) | `scholar_protocol/intent.py:126-175`; `inception/genesis.py:146-181`; `workspace_proposals.py:247-270` |
| E22 | *Read on 2026-11-21.* The terminal wizard (`scholar-harness inception`, `inception/wizard.py`) reaches genesis through `emit_workspace` and `compile_protocol_files` without step 5's screen, so it writes the model defaults | `inception/wizard.py:34-40,200`; `inception/emit.py:352,375`; `inception/genesis.py:184` |

## The contract questions (they decide whether this is small or large)

### (a) A revised criterion changes the fingerprint every decision is bound to

A pilot needs records, so it runs after the corpus is accepted and the batches are prepared (E10: a decision needs a batch binding). By then the fingerprint binds the corpus, the batches and every decision (E5). Three designs:

**A1. An amendment beside the signed protocol, like the method amendments.** `protocol.json` is not touched; a criteria amendment is one line of `audit/criteria_amendments.jsonl` and a journal row; the criteria in force are the signed list plus the amendments made under the current fingerprint, oldest first, exactly as `effective_method` reads the method (E7).
- *For:* the corpus, the batches and every decision keep their binding, so nothing is archived and nothing is screened twice for no reason. It reuses a pattern the researcher accepted on 2026-11-20 and that already reaches the methods paragraph. No Contract v1 schema changes (E16). It is how a researcher works: the protocol says what was planned, the amendments say what changed and why.
- *Against:* the fingerprint no longer fixes the criteria a decision was made under; the compass asks that downstream work be bound to "the exact protocol" (§3). That loss was accepted for the method on 2026-11-20 (H-screening-drafts item 2, which changed the 2026-11-08 rule); criteria are closer to the heart of a decision than the method, so it needs the researcher's own yes. Every reader of the criteria (agent run, draft reader, reason check, Triage, export) must read the criteria in force instead of `protocol.json`; one missed reader would screen against the old wording silently.
- *How the loss is repaired:* each amendment raises a **criteria version** (1 is the signed list). The engine stamps the version in force on every new decision event and every new draft (an engine field like `received_at`, E8), so each decision names the wording it was made under without trusting a clock. The publish step records the sha256 of the amendments file in its journal row, and the methods paragraph lists every amendment.

**A2. A new signed protocol version.** The revision is compiled into a new `protocol.json`, re-signed, with a link to the version it supersedes.
- *For:* the fingerprint keeps meaning "these exact criteria"; the compass rule holds as written.
- *Against:* the corpus snapshot and the batches are Contract v1 artifacts bound to the old fingerprint, and acceptance must reject a fingerprint-mismatched parent (compass §3, "never recompute or silently replace a parent identity"). Keeping the corpus under a new protocol needs a new contract notion, a protocol version that supersedes another and inherits its corpus and batches, or the corpus is accepted again and batches are prepared again, which makes every earlier decision count nowhere (E5, E6). Either way: a contract decision, regenerated schemas and golden fixtures, a negative regression test and an independent review (AGENTS.md, "Contract v1 baseline"). Several times the size of A1.

**A3. Both:** the amendment record, and a new fingerprint computed over the signed protocol plus the amendments, carried on new decisions. It keeps a fingerprint for the wording but has A2's cost wherever that fingerprint must bind (batches, the corpus), and A1's where it does not. No advantage over A1 with the criteria version.

**Recommendation: A1, with the criteria version stamped by the engine. Accepted by the researcher on 2026-11-21 (answer 1).**

**What happens to decisions afterwards (answers 2 and 5).** The pilot's decisions are not counted (answer 5): they are kept apart, outside the event log, and the pilot's records are screened again in the main screening ((d)). So a revision made during the pilot, or after it and before any record is decided in the main screening, **touches no counted decision**: nothing is shown again, and the dry call says "No record will be shown again." The pilot decisions made under the earlier wording stay in the pilot file with their criteria version, and the result screen labels them; they are never shown again, because their records come back in the main screening anyway.

Counted decisions exist only once the main screening has started. A revision then, still before the first approval (answer 4), works as accepted in answer 2: decisions are kept, and the ones a revision could change are **shown again**: every Include, every Unclear (MAYBE), and every Exclude whose reason cites a criterion the revision touched. An Exclude for a criterion left untouched still holds, because one failed criterion is enough. A record shown again keeps its earlier decision in the log; the new decision supersedes it (`supersedes`, E8). Until it is decided again, its batch counts as not fully decided, so it cannot be approved (fail closed: compass §3). "Carried over unchanged" was rejected: an Include made under the old wording is not an Include under the new one. ("Kept apart" was the option first argued against, because it reads 50 records twice; the researcher chose it for the cleaner separation.)

**When a revision is allowed (answer 4).** From the moment batches are prepared until the first batch is approved. Shown again applies to every counted decision; pilot decisions are not counted decisions for this rule. The confirmation states how many records it will show again. After a batch is approved, a revision is refused (`CRITERIA_AMENDMENT_AFTER_APPROVAL`); changing criteria after publication stays a new screening (start from this protocol), as today. Before batches exist a revision is refused (`CRITERIA_AMENDMENT_NO_BATCHES`); the pilot needs prepared batches too ((d)).

### (b) What happens to `EXC-03`

| Change | The id | Decisions citing it |
| :-- | :-- | :-- |
| **Reword** (same test, clearer words) | Kept: `EXC-03`. The amendment keeps the old and new text, so "EXC-03 as of version 2" is recoverable | Shown again (an Exclude citing it, every Include and Unclear) |
| **Split** into two | `EXC-03` retired; two new ids (`EXC-06`, `EXC-07`) | Shown again |
| **Merge** two into one | Both retired; one new id | Shown again |
| **Remove** | Retired | Shown again |
| **Add** | A new id | Every Include and Unclear shown again; Excludes untouched |
| A change of reason category only (`reason_category`, the "Rejection Reason Code" text) | Kept | None shown again; recorded as an amendment |

- **Ids are never reused.** A new id takes the next number on its side after every id ever used, retired ones included (`EXC-06` after `EXC-01`…`EXC-05`, even when `EXC-03` was retired). The same for inclusions, whose failure reason is `FAILS-INC-nn`.
- **A retired id is refused on a new decision** (`REASON_CODE_RETIRED`, a new refusal), and stays valid in the log on the decisions made before. After every record shown again is decided, no final decision cites a retired id, so the PRISMA "excluded, by reason" counts name only criteria in force.
- "Shown again" in the table means counted decisions (answer 5). A pilot decision citing a retired id stays valid in the pilot file and is labelled with its criteria version on the result screen; it is never shown again.
- Accepted by the researcher on 2026-11-21 (answer 3).
- *Alternative:* a new id on every change of wording, rewording included. Simpler to state, but a clarification after a pilot is the common case, and the PRISMA counts would then split one criterion across two labels. Not recommended.

### (c) Contract decision or not

Under A1 nothing in Contract v1 changes (E16):
- `protocol.json` is not written after genesis, so the protocol schema and the fingerprint algorithm do not change.
- The reason code is a harness field of the event log; the locked `ScreeningDecision` keeps a free-text `reason`. The criteria version is a new engine-stamped field of the harness event log and of `proposals.jsonl`, not of a Contract v1 schema.
- The corpus snapshot and the batch files are not rewritten. The batch file still embeds the signed wording (E10); it stays as it is because it is hashed into every binding, and every reader takes the wording in force from the engine instead.
- `audit/criteria_amendments.jsonl` and the pilot files are side files outside the baseline, like `audit/method_amendments.jsonl`.
- **Answer 5 adds nothing to Contract v1.** Pilot decisions are not decision events and are never handed to the Contract v1 collector, so the minimum screening provenance (compass §6) does not apply to them. The main decision on a pilot record is an ordinary single-screener `HUMAN` decision with no parent: the pilot decision is not its parent, and it is not a second screener's decision, so the dual-screening and adjudication rules (compass §3) do not apply. Pilot decisions get their own id prefix (`PLD-`), distinct from event ids (compass §3, Identity). No conflict with Contract v1 was found; the one possible conflict, with the harness screening API contract, is avoided by answer 11 (counts only).
- **The harness screening API contract** (`docs/architecture/screening-api-contract.md`, accepted 2026-11-04; not baseline-locked) is amended by parts A and B: the engine-stamped `criteria_version` on events (§3.1), the refusal codes (§7), the pilot and amendment routes (§4), and `PILOT_OPEN` on intake (§3.4). Each part amends that document in its own PR.

`generate_contract_baseline.py --check` must still answer "current" before and after each part.

**It is RELEASE in any case**: A1 adds public routes, refusal codes, persisted records, an engine-stamped field on decision events and drafts, and changes what decision intake accepts (`test_gate_policy.md`: public API semantics, artifact persistence). **It would also need a contract decision and a baseline regeneration** if the researcher chooses A2 or A3; if the criteria version, or the amended wording, had to appear in the published Contract v1 screening-decisions artifact (as a field, not as free text in `reason`); if the amendments file had to become a registered parent under the envelope's `inputs`; or if the PRISMA by-reason figure became a contract artifact. None is recommended.

## Scope recommendations

### (d) The pilot sample (answers 5 and 6, 2026-11-21)

**Unchanged by the answers (not questioned):**
- **Size 50** by default; the researcher can choose 20 to 100 (step 10). The note "50 to 100 records" is the usual practice; 50 keeps a solo reviewer's pilot to about half an hour at 30 seconds a record.
- **Drawn how:** simple random from the accepted snapshot's studies, with a seed the engine draws and records (`random.Random(seed).sample`, the snapshot id and the order of its studies as input, so the same seed on the same snapshot gives the same list). Drawn from records that have no decision in the main screening and are in no earlier pilot. Not stratified: a stratified draw needs strata the app does not have; records without an abstract are drawn like the others and labelled, because the full screening meets them too.
- **The draw file:** `literature/screening/pilot/pilot_NNN.json` (`pilot_id`, `seed`, `n`, the snapshot id, the protocol fingerprint, the criteria version, `drawn_at`, `drawn_by`, and the list of `{study_id, batch_id}`), journal row `SCREENING_PILOT_DRAWN`. Inside `literature/screening/`, so a chase round archives it with the rest (E17).
- **A second pilot** after a revision is allowed: 50 more records, a new seed, `pilot_002`. The result screen compares the two.

**Where pilot decisions go (answer 5: not counted).** They are **not decision events**. Each one is a line of `literature/screening/pilot/pilot_NNN_decisions.jsonl`, append-only: `pilot_decision_id` ("PLD-" + 24 hex), `pilot_id`, `study_id`, `screener_id`, `decided_at`, `outcome`, `reason_code` (the same rule as an event: required on Exclude, one id in force or `FAILS-INC-nn`), optional `criteria[{id, answer}]`, `note`, `supersedes` (a change of mind inside the pilot); the engine stamps `received_at`, `criteria_version` and `protocol_fingerprint`. There is no batch binding, because a pilot decision is not part of any batch's decided set.
- **Intake:** `POST /api/v1/screening/pilot/{pilot_id}/decisions`, which reuses the event intake's checks (`valid_reason`, `REASON_CODE_INCONSISTENT`, `REASON_CODE_RETIRED`, the input limits of H-input-limits) and refuses a study outside the pilot (`PILOT_RECORD_UNKNOWN`) or a closed pilot (`PILOT_CLOSED`). One journal row per request (`SCREENING_PILOT_DECISIONS_RECEIVED`, counts only), as the event intake does.
- **Never read by:** the winning-event projection and `batch_NNN_decisions.json`, the queue's main views and "decided" counts, the batch "fully decided" rule and approval, collect and the Contract v1 collector, PRISMA, the methods paragraph's decision counts, `GET /agreement`, and (when it is built) the ladder's calibration gate (M9b). A test: a workspace whose only decisions are pilot decisions has 0 decided records, nothing to approve, nothing collected and an empty agreement.
- **Why a separate file, not events with a "pilot" flag.** (1) The screening API contract (E19, §3.4) makes a second non-superseding event for the same study and screener with another outcome a `conflict`, which leaves the study out of the projection and blocks collect; a pilot Exclude followed by a main Include would be one. (2) Every reader of events would have to skip pilot events, and a reader that forgot would count a pilot decision: that fails open. A separate file fails closed, because a reader that does not know it never sees it.
- **While a pilot is open** (it has undecided records and was not ended): Triage opens on the pilot view, and a main decision event on one of the pilot's records is refused (`PILOT_OPEN`), so no record is decided in both places at once. The other records can be decided in the main screening meanwhile, and the main queue leaves the open pilot's records out (the refusal is the guard, not the usual path). A pilot whose records are all decided closes by itself. "End the pilot" closes it early with its undecided records left as ordinary undecided records; closing writes `SCREENING_PILOT_CLOSED` (pilot id, n, decided).
- **Back to the main screening.** When the pilot closes, its records are ordinary undecided records in their batches, in batch order. **Blind to the pilot decision (answer 11, 2026-11-21).** Triage shows nothing of the pilot decision, before or after the main decision, and the main queue does not tag pilot records; the pilot result keeps them. Showing the pilot decision beside the record would invite copying it, and the second reading would then buy nothing for its time. Showing it after the main decision would be a consistency check, but it teaches the researcher to expect it. For the agent's drafts made on the pilot, the pilot result shows counts per criterion only, never one record's draft (answer 11), so no pilot record is seen with its draft before its main decision.
- **The cost of answer 5:** every pilot record is read twice, about 25 minutes for 50 records at 30 seconds a record, once per pilot. In exchange, no pilot decision made under an earlier wording ever reaches the published screening, and a revision during the pilot shows nothing again.

**The checklist during the pilot (answer 6: closed as today).** The pilot uses Triage's checklist as the main screening does: collapsed, optional, opened on E, a number key or its toggle (decision 2026-11-09, "the checklist is a tool for the reason"). There is no pilot-specific default and no pilot-specific prompt to open it. Absent answers stay absent. What the result can then show is set out in (e).

### (e) What the researcher sees after the pilot

One screen, read from the engine (`GET /screening/pilot/{pilot_id}/result`), counts only, each with its denominator:

1. **The decisions:** n decided of N drawn; Include, Exclude, Unclear. These are pilot decisions: the screen says once that they are not counted and that the records come back in the main screening.
2. **Per criterion,** in protocol order, a row: how many exclusions it was the reason for (`EXC-nn` or `FAILS-INC-nn`; always shown). When at least one pilot decision carries checklist answers: how often the checklist answered it "not reported", of the records where it was answered. When the agent check has run on the pilot (answer 9): how often the draft answered it `not_reported`, and how often the draft and the researcher's decision read it differently ((f), "Read differently"), each of its own denominator.
3. **What this suggests,** a short list of observations, each from a fixed rule ((f), the pilot rules), each naming the criterion and the counts behind it, never an instruction: "EXC-05 was the reason for none of the 30 exclusions in this pilot of 50. It may be rare, or covered by another criterion." Each has one action "Revise {id}" per criterion it names (two for a pair) and nothing else. The readings that could not be computed are listed by name with what they need (below).
4. **Records,** filterable by criterion (the reason code) and by your pilot outcome: the titles, opening the record read-only with its pilot decision. Not filterable by the agent, and no per-record draft is shown (answer 11).
5. **The action bar:** "Revise a criterion" (opens the revise dialog), "Pilot 50 more records", "Screen the rest". "Screen the rest" records nothing; it goes to the main queue, where the pilot records wait like any other.

**What can be shown with the checklist closed (answer 6).** Each pilot decision always gives an outcome and, for an Exclude, exactly one reason code. Per-criterion answers come only from the checklist when the researcher opens it, or from the agent check on the pilot (answer 9). So:

| Reading ((f)) | From the decisions alone | Needs the agent check | With checklist answers, when given |
| :-- | :-- | :-- | :-- |
| Many Unclear | yes | | |
| Does most of the work | yes (reason codes) | | |
| Never used | weaker form: "was the reason for none of the exclusions" | full form: and the agent never answered it against | full form, on the answered records |
| Hard to judge from the abstract | no: an Unclear names no criterion | yes (the draft's `not_reported`) | yes (the checklist's "not reported") |
| Exclusions that fire together | no: an Exclude cites one reason only | yes | yes |
| Mirrored pair | no | yes (only from the draft's answers) | no (too few answers for the rule) |
| Read differently | no | yes, against what your decision implies (below) | yes, against your answers |

**When the researcher neither opens the checklist nor runs the agent check**, the result shows the decision counts, per criterion the exclusions it was the reason for, and at most three readings: many Unclear, does most of the work, and never used in its weaker form. Under them one line names the four it could not compute: "Four readings need answers per criterion: hard to judge, fire together, mirrored pair, read differently. Let the agent check these {n} records ({estimate}), or open the checklist while you screen a second pilot." The mirror of the 2026-11-20 review (EXC-02 against INC-02) is **not** shown in that case; the screen says so in Details, not as a warning.

**"What your decision implies"** (used by "Read differently" without checklist answers): an Exclude citing `EXC-n` implies `EXC-n` met; one citing `FAILS-INC-n` implies `INC-n` not met; an Include implies every inclusion met and no exclusion met; an Unclear implies nothing. The column says "against your decisions, not answers per criterion". It is an inference from the outcome, labelled as such; a disagreement read this way is weaker evidence than one against an answer.

**After a revision** the result keeps each pilot's numbers with the criteria version its decisions were made under; it is recomputed when read, never stored. Pilot decisions are not shown again (answer 5). **There is no undo:** a revision is reversed by another revision (a reword back, an add), and both stay in the record.

A pilot of 50 is small: a criterion that applies to 2% of records is expected once. The screen says so once, under the table: "Counts from 50 records. A criterion that decided nothing here may still matter in the full corpus."

### (f) The criteria lint

Two kinds of check, both plain rules, none a model, none a blocker.

**Before any record (Inception, on the wording), new checks in the M10b catalogue (`02-checks.md`):**

| Check | Rule | Level |
| :-- | :-- | :-- |
| `CRITERIA_DUPLICATE` | Two accepted criteria on the same side whose normalised texts are equal (lower case, punctuation and stop words removed) | warning |
| `CRITERIA_CONTRADICT` | An inclusion and an exclusion whose normalised texts are equal: a record cannot meet one without failing the other | warning |
| `CRITERIA_MIRRORED` | An exclusion whose content words, after removing the negation words (not, no, without, only, other than, non, except, excluding), cover at least 0.6 of an inclusion's content words (or the reverse) | warning |
| `CRITERIA_LUMPED` | A criterion with a semicolon, or a list of three or more items joined by commas and "or" / "and" | note |
| `CRITERIA_NEEDS_FULL_TEXT` | A criterion naming something an abstract rarely reports, from a fixed word list (full text, results section, table, sample size, code available, data available, statistical test, reports the …); the list is a constant | note |

The checks read accepted criteria only (undecided wizard criteria are read when accepted). The negation list, the stop words and the full-text word list are English; for a review whose criteria are in another language only `CRITERIA_DUPLICATE` and `CRITERIA_CONTRADICT` (equality after normalising) run, and the checks panel says the other three were not run. With D6 the out-of-scope question leaves Shape; an existing draft's out-of-scope items are kept and shown in the criteria block.

What these rules cannot do: "RGB only" against "multispectral imagery from a UAV" share no word, so `CRITERIA_MIRRORED` does not catch the run's own mirror; "uses a learned model" against "or a dataset paper" is a contradiction of meaning. Both need a reader of meaning.

**After the pilot (on the answers), the observations of (e):**

| Observation | Rule (constants; n is the number of records where both answers exist) | Needs (answer 6) |
| :-- | :-- | :-- |
| Mirrored pair | Agent drafts: an exclusion answered `yes` exactly when an inclusion is answered `no`, in at least 90% of n ≥ 10 records | the agent check |
| Exclusions that fire together | Agent drafts or checklist: two exclusions both `yes` in at least 90% of the records where either is `yes` (at least 5) | the agent check, or checklist answers |
| Hard to judge from the abstract | A criterion answered `not_reported` in at least half of the drafts, or of the checklist answers (n ≥ 10) | the agent check, or checklist answers |
| Never used | A criterion that was the reason for no exclusion; in its full form also never answered against (exclusion never `yes`, inclusion never `no`) | nothing (weaker form); the agent check or checklist (full form) |
| Does most of the work | One criterion was the reason for at least 60% of the exclusions (informative; says "check it is worded as you mean") | nothing |
| Many Unclear | At least 30% of the pilot decided Unclear | nothing |
| Read differently | The draft and the researcher disagree on a criterion in at least 25% of n ≥ 10 records; the researcher's side is a checklist answer when given, else what the decision implies ((e)) | the agent check |

With the checklist closed (answer 6) the pilot rules catch the run's mirror only through the agent check (answer 9), from answers the agent already gives per criterion (E11): a model call, about $0.01 for 50 records on Haiku 5.5, behind its own confirmation. Without it, nothing in M11b sees a mirror of meaning. **Recommendation: rules only in M11b** (accepted, answer 7). A meaning check would need a model call at Inception, its spend approved, its errors measured; the M10c critic over MCP can already be asked by the researcher's own AI client (not yet tried with a real client), and an in-app critic belongs with M10e. There is no strong reason to bring a model into this milestone.

### (g) Inception asks the two method settings

On step 5, in the criteria block after the two lists, a short section "How you will screen", two questions with words that say what each choice costs. Stored in the draft (`method_blinding`, `method_not_reported`, new), written by genesis into the protocol's `method` block (today genesis writes the defaults, E2). Both can still be amended later from Prepare (E7).

1. **"When should the agent's draft for a record be shown to you?"** (not questioned separately by the researcher; **the pre-selection below is a proposal**)
   - "After you decide the record" (`reveal_after_decision`) · pre-selected, as today. Help: "You read each record without the agent's view first, and the app can measure how often the agent agrees with you."
   - "Beside the record, while you decide" (`show`). Help: "Faster to screen. The app can then not measure the agent against your own reading, because you saw its draft first."
2. **"When the title and abstract do not report a criterion, the agent's draft should…"** · **no option pre-selected (answer 8).** Listed from the most cautious to the strictest, each with the same kind of cost words:
   - "Mark it Unclear whenever a criterion is not reported" (`unclear`). Help: "The most cautious. On the measured set of 1,644 records the agent's include recall (lower bound) was 96.8% and it caught 1.9% of the excludes; in the 2026-11-20 review 85% of drafts were Unclear."
   - "Exclude only on a clear failure; otherwise mark it Unclear" (`decisive_first`). Help: "A record that clearly fails one criterion is excluded even if another is not reported. On the measured set: include recall (lower bound) 92.2%, 78.6% of the excludes caught."
   - "Exclude when an inclusion criterion is not reported" (`exclude`). Help: "The strictest. A record is excluded when its abstract is silent on something it must show. Not measured." (The model's definition: an inclusion criterion not reported gives Exclude, `FAILS-INC-n`; `scholar_protocol/models.py:342-347`.)

**What "no rule chosen" means (answer 8).**
- **A new draft** stores `method_not_reported: null`. Step 5 shows no selection, and a new blocker check, `METHOD_RULE_UNCHOSEN`, sits in the M10b catalogue at the field and at Review, like `CRITERIA_UNDECIDED`: step 5 cannot be passed and genesis is refused through the existing blocker path until one of the three is chosen. A blocker, so not dismissible.
- **A draft started before part D** has no rule either and meets the same blocker, with one extra sentence: "This draft was started before this question existed." One choice clears it. (This replaces the first draft's "shows the model defaults until you choose".)
- **An imported protocol** (`09-start-from-protocol`) with a `method` block fills both questions from it, shown as chosen with "From the imported protocol"; without a block the rule is unchosen and blocks.
- **The step API:** `GET` of the draft answers `method_not_reported: null` until chosen; the draft write accepts only the three values (not `null` once chosen); the preview's checks list the blocker; genesis is refused with the existing blocker refusal naming `METHOD_RULE_UNCHOSEN`. The M10c assistant over MCP only proposes (`nexus_assistant_propose`, `src/scholar_agent/server.py:2317`) and gets no proposal kind for the rule: the choice is the researcher's.
- **The value travels in the intent, not only in genesis (found in the rework, E21).** `compile_intent` fills the model defaults whenever the intent carries no method, and the search amendment of M10c 9(a), which M11a's "Change the search" uses, recompiles the intent and refuses any change outside the search fields. A review whose researcher chose `decisive_first` would therefore have every later search amendment refused (`outside_search`, the method block differs). Part D writes the two choices into `intent.json` as an additive `method` entry that the compiler copies, so genesis and every recompile give the same block. This also held for the first draft's recommendation and was missed there.
- **Existing reviews** (a protocol already signed) do not change and are not asked: their rule is the signed value, or the model default `unclear` for a protocol without a block (decision 2026-11-08), and it stays changeable by the method amendment on Prepare (H-screening-drafts item 2). The model's default in `MethodConfig` stays `unclear`, so no fingerprint moves.
- **The terminal wizard** (`scholar-harness inception`, E22) reaches genesis without step 5's screen. It asks the same question with no default (a numbered choice, asked again until answered), and a non-interactive run needs `--not-reported <rule>` and refuses without it (answer 12, 2026-11-21).

**Accepted decisions answer 8 meets.** H-screening-drafts (2026-11-20) item 1: "`unclear` stays the default and the value genesis writes, so no existing protocol changes"; item 9: "Inception does not ask. Genesis still writes `blinding: reveal_after_decision` and `not_reported: unclear` without asking"; and 2026-11-08, "New workspaces are written with the block, filled with today's values." Answer 8 changes the genesis half of item 1 and the 2026-11-08 sentence for the not-reported value of reviews made at step 5 (genesis writes the researcher's choice), and closes the follow-up of item 9. "No existing protocol changes" still holds. The researcher's answer is the decision that changes them; the decisions entry records it as a change. Answer 12 extends it to the terminal wizard.

### (h) How a revision is recorded and reported

**The amendment row** (`audit/criteria_amendments.jsonl`, one line per revision): `amendment_id` ("CRA-" + 24 hex), `op` (`reword`, `split`, `merge`, `remove`, `add`, `reason_category`), `side`, `from` (list of `{id, text, reason_category}`), `to` (same), `reason` (one sentence, required, at most 500 characters), `criteria_version_before`, `criteria_version_after`, `protocol_fingerprint`, `pilot_id` (the pilot in progress, or null), `decided_at_time` (how many decided records existed), `shown_again` (how many, by outcome), `amended_by`, `amended_at`.

Under answer 5, `shown_again` counts counted decisions only, and is zero for a revision made before the main screening starts.

**Journal rows:** `SCREENING_PILOT_DRAWN` (pilot id, n, seed), `SCREENING_PILOT_DECISIONS_RECEIVED` (counts), `SCREENING_PILOT_CLOSED` (pilot id, n, decided), `PROTOCOL_CRITERIA_AMENDED` (amendment id, op, from and to ids, the reason, the versions, the counts), and on publish the sha256 of `audit/criteria_amendments.jsonl` in the publish row. `SCREENING_CRITERIA.md` is rewritten as the criteria in force with a section "Amendments" listing each one; the earlier file is backed up to `audit/amended/<UTC stamp>/` as M10c 9(a) does.

**The methods paragraph** (`screening/export.py` `build_methods`, E14) gains, after the method sentences:
- with a pilot (answer 5): "The screening criteria were piloted on {n} records drawn at random from the {N} records of the corpus (seed {seed}){, and on {n2} more after the first revision}. The pilot decisions were not counted; these records were screened again with the rest of the corpus{, without the pilot decision in view}." (The last clause holds by answer 11.)
- per amendment: "On {date}, {criterion} was {reworded | split into … | merged with … | removed | added}: '{from}' became '{to}'. Reason: {reason}." Then, when counted decisions existed: "{k} records already decided were screened again." When none did: "It was made after the pilot and before the main screening." When it came during the main screening: "… after {d} records had been decided …".
- with no amendment: "The criteria were not changed after the protocol was signed."

The PRISMA figure is unchanged in shape; its "excluded, by reason" counts name the criteria in force (b).

### (i) What "check the agent on your labels" reuses from the pilot

Accepted (answer 9). The pilot's decisions are the labels. Under answer 5 they are not decision events, and the calibration route refuses a study with no decision in the event log (E20). So the route gains an additive body field `pilot_id`: with it, the study ids are the pilot's decided records and the reference labels are read from the pilot file; without it, the route is unchanged. The drafts are stored as today (`kind: calibration`) with the `pilot_id`. "Check the agent on these 50 records" on the result screen calls it, and always sends a model: the setup's `last_model` (`GET /proposals/setup`), else the run screen's constant `claude-haiku-5-5` (H-screening-drafts item 6). The route's body defaults to Opus 5.5, and the screen must never rely on that default (the $7.59 of finding 32). The dialog names the model, the count and the estimate, which comes from the existing `POST /proposals/runs {estimate_only: true, scope: {study_ids}}` (`console/api/screening_v1.py:987-1042`); about $0.01 for 50 records on Haiku 5.5 (scaled from the run's $0.22 for 1,062). The result fills the agent columns of (e) and the per-criterion disagreement, as counts; no per-record draft is shown on the pilot result (answer 11). These drafts are the latest drafts of the pilot records, so in the main screening they are shown as any draft is, under the blinding in force. `splits_by_criterion` (E12) gains its denominator. `prompt-gate measure --scope all` stays the command-line route and is unchanged. Drafts made under an earlier criteria version are labelled "made under the earlier wording" and are not counted in agreement, calibration or the queue's order; the run screen offers "Draft again the {n} records whose draft predates the revision", with its estimate. No spend happens without that dialog.

## Definition of done

Each item is checked by a test named in the build record, unless it says "live".

**Criteria amendments (part A)**
- [ ] DoD 1. `POST /api/v1/screening/criteria/amendments {op, side, ids, text?, reason_category?, reason, confirm}` (desktop only) records a revision: one line of `audit/criteria_amendments.jsonl`, one `PROTOCOL_CRITERIA_AMENDED` row; `protocol.json`, the snapshot and the batch files keep their bytes.
- [ ] DoD 2. The criteria in force are the signed list plus the amendments under the current fingerprint, oldest first, with a version number; one function reads them, and every reader uses it: the agent run, the draft reader, the reason check at intake, Triage's criteria and checklist, the batch instructions shown to an agent, the agreement read, the export. A test lists the readers of `screening_criteria` and fails on a new one that bypasses the function.
- [ ] DoD 3. Ids follow (b): reword keeps the id; split, merge and remove retire; a new id takes the next number on its side, never a used one; `REASON_CODE_RETIRED` on a new decision citing a retired id; earlier events stay valid.
- [ ] DoD 4. Every new decision event and every new draft carries the engine-stamped `criteria_version`; an event without it is version 1. A browser cannot send it.
- [ ] DoD 5. After an amendment, the records shown again are exactly: Include, MAYBE, and Exclude citing a touched criterion, for counted decisions (event log, never pilot decisions) made under an earlier version; the queue lists them (`view=recheck`); a batch holding one is not fully decided for approval.
- [ ] DoD 6. A revision is refused before batches exist (`CRITERIA_AMENDMENT_NO_BATCHES`), after a batch is approved (`CRITERIA_AMENDMENT_AFTER_APPROVAL`), without a reason or `confirm`, for an unknown or retired id, or one that changes nothing (`CRITERIA_AMENDMENT_INVALID`). A dry call (`confirm: false`) answers what it would change: the new ids and how many records it would show again, by outcome.
- [ ] DoD 7. A revision that leaves a side with no criterion in force is refused (`CRITERIA_SIDE_EMPTY`), as genesis refuses a missing side.
- [ ] DoD 7b. `GET /api/v1/screening/criteria` answers the criteria in force (id, side, text, reason category, the version each wording dates from), the retired ids, the current version and the amendments; the revise dialog and Triage read it.
- [ ] DoD 8. `SCREENING_CRITERIA.md` is rewritten with the criteria in force and an "Amendments" section; the earlier file is backed up under `audit/amended/<stamp>/`.
- [ ] DoD 9. Drafts made under an earlier version are labelled and left out of agreement, calibration and queue order; the run setup counts them.
- [ ] DoD 10. The methods paragraph reports each amendment and, with no amendment, says the criteria were not changed; the publish journal row carries the sha256 of the amendments file.

**The pilot (part B)**
- [ ] DoD 11. `POST /api/v1/screening/pilot {n, confirm}` draws n (20 to 100, default 50) records with no main decision and in no earlier pilot, at random with a recorded seed; the same seed on the same snapshot gives the same list; the draw file and `SCREENING_PILOT_DRAWN` are written. Refused before batches exist, after a batch is approved, while another pilot is open (`PILOT_OPEN`), or when fewer such records remain than asked. A dry call (`confirm: false`) answers n, the count left to draw from and the expected time, and writes nothing.
- [ ] DoD 11b. `GET /summary` gains a `pilot` block (the open or last pilot's id, n, decided, open or closed, and how many counted records wait to be shown again), so every screen knows a pilot is open without a new route.
- [ ] DoD 11c (answer 5). `POST /api/v1/screening/pilot/{id}/decisions` writes pilot decisions to `pilot_NNN_decisions.jsonl` (fields of (d), ids `PLD-…`, engine-stamped `criteria_version`, fingerprint, `received_at`), with the event intake's reason checks; refuses `PILOT_RECORD_UNKNOWN`, `PILOT_CLOSED`. A test shows a workspace with only pilot decisions has 0 decided records, nothing approvable, nothing collected, an empty `/agreement` and no change to any `batch_NNN_decisions.json`.
- [ ] DoD 11d (answer 5). While a pilot is open, a main decision event on one of its records is refused `PILOT_OPEN`; "End the pilot" (`POST /pilot/{id}/close`) closes it and writes `SCREENING_PILOT_CLOSED`; afterwards the pilot records are ordinary undecided records, and no main-screening answer (queue, record, Triage) carries their pilot decision (answer 11).
- [ ] DoD 12. `GET /queue?view=pilot` lists the pilot's records in the drawn order. The checklist keeps the 03 default (collapsed) in the pilot (answer 6).
- [ ] DoD 13. `GET /screening/pilot/{id}/result` answers (e): counts per outcome; per criterion the exclusions it was the reason for; the checklist's `not_reported` when answers exist; with the agent check the draft's `not_reported` and "read differently", each with its denominator and its source (answers or implied); the observations of (f) with their counts, and the names of those not computed with what they need; for a second pilot, the first one beside it. No per-record draft (answer 11).
- [ ] DoD 14. "Check the agent on these records" calls `POST /proposals/calibrations` with `pilot_id` (new, additive) and an explicit model, always (a UI test fails when the body has no `model`); without `pilot_id` the route is unchanged; the estimate comes from `POST /proposals/runs` with `estimate_only` and the same ids. The route's own Opus default is not changed here (a public default; changing it is a separate decision).
- [ ] DoD 15. `splits_by_criterion` gains `answered_by_both` per criterion; old clients still read the count.

**Screens (part C)**
- [ ] DoD 16. Prepare offers "Pilot your criteria first" beside "Screen everything", per the screen spec; Triage shows the pilot's banner and progress; the result and revise screen and its dialog follow `13-criteria-pilot.md`; every state has its words in en, fr and ar; axe passes in light and dark.
- [ ] DoD 17. The revise dialog shows, before anything is recorded, the new ids and the records it will show again by outcome, and needs the reason.

**Inception (part D)**
- [ ] DoD 18. Step 5's criteria block asks the two method settings with the words of (g): draft visibility pre-selected "after you decide" (proposed), the not-reported rule with **no option pre-selected** (answer 8). `METHOD_RULE_UNCHOSEN` blocks step 5, Review and genesis for a new draft, a draft from before part D and an import without a method block; the draft write accepts only the three values; genesis writes the choice into `method`; the preview lists it.
- [ ] DoD 18b. The two choices are stored in `intent.json` and copied by the compiler, so a search amendment (M10c 9(a), M11a) of a review that chose `decisive_first` or `exclude` is not refused `outside_search` (a regression test). A protocol without the choice keeps its fingerprint.
- [ ] DoD 18c (answer 12). The terminal wizard asks the rule with no default; a non-interactive run without `--not-reported` is refused before anything is written.
- [ ] DoD 19. The five wording checks of (f) in the catalogue, at the field and at Review, never blockers, dismissible with a reason (M10b rule).
- [ ] DoD 20. The criteria are laid out as direction A's criteria block (D13) inside today's step 5, as M11a did for the concepts block; the out-of-scope question is asked in this block (D6).

**Closure**
- [ ] DoD 21. `generate_contract_baseline.py --check` current before and after each part; `generate_protocol_schema.py --check` unchanged.
- [ ] DoD 22 (live). The researcher pilots the criteria of a real review (50 records), revises at least one criterion, screens the pilot records again in the main screening, and reports in this record what the pilot showed, whether the observations were right, and how many pilot records were decided differently the second time.

## In and out

**In.** The pilot draw, its queue and result; the observations by rule; criteria amendments beside the signed protocol (reword, split, merge, remove, add, reason category) with the criteria version, the records shown again and the approval gate; the methods sentences; the calibration on the pilot; the five wording checks at Inception; the two method questions at Inception; the criteria block (D13) and the out-of-scope question moving to it (D6).

**Out, and where it goes.**
- Any language model in the lint or the observations. The M10c critic over MCP is the researcher's own client's job today; an in-app critic waits with M10e.
- A new signed protocol version (A2, A3): only if the researcher chooses it; then a contract decision first.
- Revising criteria after a batch is approved, or in a citation-chasing round: a new screening, as today.
- Full-text screening and its reasons (PRISMA asks reasons at full text): M12a or later.
- A second human reviewer on the pilot (the supervisor's sample check): the existing sample check on Agreement is unchanged; dual screening is not in scope.
- Changing the concepts or the search: M11a (Plan's "Change the search", before a corpus is accepted).
- The frame of direction A (M10f-1), D4 (checks with proposals) and the rest of M10f-3 beyond the criteria block.
- `prompt-gate measure` changes; per-criterion output there.
- A figure comparing each pilot decision with the later main decision on the same record (a same-reader consistency check): possible from the two files after answer 5, not shown in M11b; DoD 22 asks for it once, by hand.
- Prompting existing reviews to choose the not-reported rule (answer 8 applies to drafts, not to signed protocols).

## Parts, one PR each

| Part | Contents | Lane | Why that lane | Size after the answers | Depends on |
| :-- | :-- | :-- | :-- | :-- | :-- |
| **A. Criteria in force** | `screening/criteria.py` (criteria in force, versions, retired ids, shown-again set), the amendment route and file, refusal codes `CRITERIA_AMENDMENT_INVALID`, `CRITERIA_AMENDMENT_NO_BATCHES`, `CRITERIA_AMENDMENT_AFTER_APPROVAL`, `CRITERIA_SIDE_EMPTY`, `REASON_CODE_RETIRED`; every reader moved to it; `criteria_version` on events and drafts; `view=recheck` and the approval gate; `SCREENING_CRITERIA.md`; the methods sentences; the screening API contract amended | RELEASE | public route and refusals, persisted record, new engine field on events, decision intake changes | **Large, unchanged.** Answers 1 to 4 were as recommended. Answer 5 makes the shown-again path rarer (only after the main screening starts), not smaller: it must still be built and tested | none |
| **B. The pilot** | `screening/pilot.py` (draw, result, observations with their sources, implied answers), the pilot decision file and its intake route (reusing the event checks), `PILOT_OPEN` on main intake, `POST /pilot/{id}/close`, `PILOT_RECORD_UNKNOWN`, `PILOT_CLOSED`, the journal rows, `pilot_id` on the calibration route, `answered_by_both`, the methods sentence; the test that pilot decisions reach no counted reader | RELEASE | public routes, a second decision intake, persisted records, an additive field on a public route | **Large (was medium).** Answer 5 adds a second decision store and intake, the main-intake refusal, the close and the calibration's second label source; answer 6 adds the source column and implied answers and removes the checklist setting | A |
| **C. Screening screens** | Prepare's entry, Triage in pilot mode (posting to the pilot route, banner, End the pilot), the recheck view, the result and revise screen with the "not computed" line (spec `13-criteria-pilot`), the run screen's "Draft again", en/fr/ar, axe | STANDARD (UI) | browser only, over A and B | **Medium, a little larger.** Triage gains a second posting target; it loses the checklist default | A, B; M8b-triage-highlights is merged (PR #271), so C builds on it |
| **D. Inception step 5** | the criteria block (D13), the out-of-scope question in it (D6), the method questions with no rule pre-selected, `METHOD_RULE_UNCHOSEN`, the method in `intent.json` and the compiler, genesis, the five wording checks (spec `11-criteria-block`); the terminal wizard's question and `--not-reported` (answer 12) | RELEASE | the inception draft API, the intent packet and the protocol genesis writes change; new check ids in a public preview | **Medium (was small to medium).** Answer 8 adds a blocker, the intent field and its recompile test, and the terminal wizard (a small CLI change) | M11a part C merged |

**The order A, B, C, D still holds.** B's pilot decisions carry A's criteria version and its "Revise" needs A's route; C draws over A and B; D waits for M11a part C, which is not merged yet. Answer 5 would allow one other order: B before A, as a pilot without revision. It is not proposed: a pilot that shows a problem and offers no way to fix it sends the researcher to "archive and start clean". In all, the milestone is somewhat larger than about M10b, mostly in B.

Inner and checkpoint gates by `scripts/select_test_gate.py --changed main`; the full suite once per PR. No live call and no model call in any test: drafts and calibration through the existing doubles.

## Reused and new

| Need | Reused | New |
| :-- | :-- | :-- |
| An amendment beside the signed protocol | the method amendment pattern: file, journal row, fingerprint filter, values in force, methods sentence (E7) | `criteria_amendments.jsonl`, ops on criteria, versions, retired ids |
| Superseding a decision | `supersedes` on decision events (E8) | the shown-again set and `view=recheck` |
| Pilot decisions (answer 5) | the event intake's checks (`valid_reason`, `REASON_CODE_INCONSISTENT`, input limits), the append-only line format, the journal row per request | the pilot decision file, its route, `PILOT_OPEN` on main intake |
| Fail closed before approval | the "fully decided" rule of approval (09-publish) | a record shown again counts as undecided |
| Reason codes | `valid_reason` (E8), `FAILS-INC-nn` | reads the criteria in force; `REASON_CODE_RETIRED` |
| Draft outcome under the rule in force | `outcome_in_force` (E11) | criteria version on drafts; earlier-wording label |
| Per-criterion answers | agent draft answers (E11), the optional checklist (E9) | the pilot's rules |
| Agreement per criterion | `splits_by_criterion` (E12) | its denominator |
| Check the agent on your labels | `POST /proposals/calibrations` (E13) | called with the pilot's ids and an explicit model |
| Checks at Inception | the M10b catalogue and `_criteria_checks` (E15) | five wording checks |
| Method at genesis | `MethodConfig` and genesis's method block (E2) | two draft fields, two questions, `METHOD_RULE_UNCHOSEN`, a `method` entry in the intent (E21) |
| Backup of a rewritten criteria file | M10c 9(a) `audit/amended/<stamp>/` | none |
| Layout | M11a part C's block, evidence column and suggestion look (D5, D13) | the criteria block |

## What it assumes from M11a, and why its build waits for M11a part C

M11a part C (`docs/ux/phase0-inception/final/10-query-workbench.md`, FINAL) rebuilds the top of the same page, Inception's step 5 (`/inception/criteria`, `components/inception-criteria.tsx`). It assumes:
1. **The block.** M11a draws the concepts block as direction A's block (open or written, one open at a time) inside today's page, and says "the other cards of 05 stay as they are until M11b". Part D draws the criteria block the same way and reuses that component.
2. **The suggestion look (D5).** M11a builds the "not yet yours" look for suggested terms; the wizard's criteria and the wording checks use it.
3. **The brand button rule on step 5.** M11a settled it (2026-11-21, question 1): "Use this version" while a concept version has unused edits, else Continue or Accept. Part D adds no brand button of its own; the method questions are radio groups.
4. **No change to the criteria by M11a.** M11a's amendment from Plan changes the search, rewrites `SCREENING_CRITERIA.md` without changing the criteria, and is refused once a corpus is accepted; M11b's amendments start only after batches exist. The two never act at the same time. If M11a's rewrite of `SCREENING_CRITERIA.md` and part A's rewrite share one renderer, part A uses M11a's.

Part D edits the same component and the same copy file as M11a part C; building it before C is merged means two branches rewriting one screen. Parts A to C touch no Inception file, so by dependency they could start earlier; under the agreed rule of at most two milestones in flight (M11a and M8b are being built now) the whole build waits anyway, and the researcher decides when it starts.

## Risks

1. **A reader left on the signed wording.** One place that still reads `protocol.json`'s criteria (a batch file, a prompt, an export) would screen or report against the old text with no error. DoD 2's test is the defence; part A starts by listing every reader.
2. **The fingerprint means less.** Under A1 a decision's fingerprint does not fix the wording; the criteria version and the amendments file do. If the amendments file is lost or edited by hand, the wording of earlier decisions is lost. Its sha256 at publish makes an edit visible, not impossible.
3. **Overfitting the criteria to 50 records.** Observations from a small sample can mislead; the screen states the sample size and never proposes a wording.
4. **Re-checking costs time.** An Include or Unclear is shown again after any revision; a revision late in the screening could show hundreds. The dry call states the number before the researcher records it.
5. **Spend.** The calibration on the pilot and "Draft again" cost money; the calibration route defaults to Opus 5.5 (E13). The screen must always send a model and show the estimate.
6. **Collisions.** Part C touches Triage, which M8b-triage-highlights is changing; part D touches step 5, which M11a part C is changing; the approval gate touches the approve-all flow of H-run-small-fixes Part A (merged).
7. **The method choice (answer 8).** No rule is pre-selected, so the researcher weighs the trade (include recall lower bound 96.8% under `unclear` against 92.2% under `decisive_first` on the measured set; drafts that decide) without a recommendation on the screen; on a different review the trade may differ.
8. **A pilot decision counted by mistake (answer 5).** A reader that read the pilot file as decisions would count records twice. The pilot file is apart and DoD 11c's test is the defence.
9. **The pilot without answers (answer 6).** With the checklist closed and no agent check, the result shows three readings and misses a mirror of meaning; the screen names what it could not compute.
10. **Search amendments refused after a chosen rule (E21).** Without DoD 18b, a review that chose a rule other than the model default could no longer change its search.

## What cannot be verified without a real review

- Whether 50 records show anything the researcher did not already know, and whether the observation thresholds (90%, 50%, 60%, 30%, 25%) are useful or noisy.
- Whether the wording checks find anything in real criteria; the run's own mirror shares no word and is caught only by the pilot rules.
- How many records a real revision shows again, and how long the re-check takes.
- Whether drafts after a revision become less Unclear (needs a paid run).
- How the researcher wants a revision worded in a methods section; the sentences above are a proposal.
- DoD 22: the researcher's own pilot.

## Open questions

All twelve are answered (table at the top). Questions 11 and 12 came from answers 5, 6 and 8 and were answered on 2026-11-21, both as recommended; they are kept below with the text they met.

**11. Blinding of the pilot records in the main screening (answers 5 and 9). Answered: "Counts only" (a).** Answer 5 sends the pilot records back to the main screening; answer 9 lets the agent check them during the pilot. The texts this meets, in the accepted screening API contract (2026-11-04, §3.1): "`proposal_shown` is `null` when the researcher decided before any proposal was revealed. With blinding on (the default) it is always `null` at decision time" and "A reveal (M1b-0) is the first time `GET /records/{id}/proposal` returns a proposal to a screener." If the pilot result showed the agent's draft for a record, the later main decision on it would be made after seeing a draft, yet its event would say `proposal_shown: null` and no reveal would be recorded; the methods paragraph would count it as blind ("Drafts were hidden until the reviewer decided"). Options:
- (a) **Recommended, chosen:** the pilot result shows the agent per criterion as counts only, never per record, and the records list cannot be filtered by the agent; the main screening shows nothing of the pilot decision either. Nothing in the contract changes. Cost: the researcher cannot see which records the agent read differently.
- (b) The pilot result shows a record's draft on request and records that as a reveal (a second reveal route), so the main decision counts as made after a reveal. This amends the contract's definition of a reveal; up to 50 records leave the blind comparison.
- (c) Show freely and report pilot records as decided with the draft visible. Amends the contract's `proposal_shown` rule for these records.

**12. The terminal wizard (answer 8). Answered: "Yes, it asks too".** Does "No default; I must choose" also apply to `scholar-harness inception` (E22)? It meets H-screening-drafts item 1 ("`unclear` stays the default and the value genesis writes") and the 2026-11-08 sentence "New workspaces are written with the block, filled with today's values." Recommended: yes; the wizard asks with no default, and a scripted run needs `--not-reported <rule>` (DoD 18c). Otherwise a review made in the terminal still gets `unclear` without a question.

The two screen drafts carry their own screen-level questions, settled when each spec is made FINAL at the start of its part.

## What the main session must change (not edited on this branch)

- Plan §6, row 4 (M11b): status "specification answered 2026-11-21 (answers 5, 6, 8 against the recommendation; 11 and 12 as recommended)" and the build state as the main session knows it; lane "A, B, D RELEASE; C STANDARD" instead of "to be declared".
- Plan §8: nothing.
- `docs/decisions.md`, the "Open decisions" table at the top: nothing for the specification (questions 11 and 12 are answered); part A's build added its row; items 1 to 11 were answered by the researcher on 2026-11-21, so the row is gone.
- At build time, not now: `docs/architecture/screening-api-contract.md` (parts A and B), `docs/ux/shared/final/02-checks.md` (the five checks and `METHOD_RULE_UNCHOSEN`, part D), `docs/ux/phase2-screening/final/03-triage-desktop.md` (pilot mode, part C).

## Build record

The researcher approved the build start on 2026-11-21 (building, not pushing). Parts in order A, B, C, then D, each its own branch and PR, stacked.

### Part A: criteria in force

Branch `dev/m11b/part-a-criteria-in-force` from the specification's final head `9f7666db`, with `origin/main` merged (`dacabd94`, then `86da80f4`, M11a part C) · Lane **RELEASE** (as declared: public routes, refusal codes, a persisted record, an engine-stamped field on decision events and drafts, decision intake changes) · Decisions: `docs/decisions.md` "2026-11-21 — M11b part A: criteria in force, the build's choices" items 1 to 11 (answered by the researcher 2026-11-21: ten accepted as built, item 5 changed to "bind the version").

What was built:
- `src/scholar_harness/screening/criteria.py`, the one reader: `criteria_in_force` (the signed list plus the amendments under the current fingerprint, oldest first; `until` for the methods paragraph), `CriteriaInForce` (version, criteria with the version each wording dates from, retired ids, every id ever used), `plan_amendment` (pure: reword, split, merge, remove, add, reason category, and the refusals), `shown_again` (Include, Unclear, and an Exclude citing a touched criterion, for a decision made under an earlier version; a reason-category change shows nothing), `amend_criteria` (under the events lock: the dry call; one line of `audit/criteria_amendments.jsonl`; `SCREENING_CRITERIA.md` rewritten through the protocol kit's renderer with an "Amendments" section, the earlier file backed up under `audit/amended/<stamp>/`; every projected batch file rebuilt; one `PROTOCOL_CRITERIA_AMENDED` row; any failure before the journal row takes every write back).
- `screening/events.py`: the context reads the criteria in force; `criteria_version` is an engine field (stamped at intake, refused from a client, read as 1 when absent); the criteria are re-read under the lock; `REASON_CODE_RETIRED` and "a record shown again must be superseded" apply to new events only; the projection leaves out a decision shown again, so approval and collect refuse its batch.
- `console/api/screening_v1.py`: `GET /screening/criteria` and `POST /screening/criteria/amendments` (desktop only; the dry call); `view=recheck`; `/summary` gains `criteria_version` and `recheck`; `/records/{id}` answers the criteria in force with `since_version`, `criteria_version` and `shown_again`; the draft read answers `criteria_version` and `earlier_wording`; agreement, the agent-uncertainty order and the calibration score leave earlier-wording drafts out; `/proposals/setup` counts them (`earlier_wording_drafts`); the run estimate builds its prompt from the criteria in force.
- `screening/agent_runs.py`: the prompt names the criteria in force; the run records its version and stamps its drafts with it. `screening/proposals.py`: `Criteria.from_in_force`, `draft_version`, the stamp on every draft; a draft of an earlier version keeps its stored outcome; the draft id names the version from 2 on (decision item 3).
- `scholar_agent/server.py`: the MCP record tool answers the criteria in force and the version. `screening/worker.py`: the file hand-off worker refuses `CRITERIA_AMENDED_USE_ENGINE` once the criteria are amended (decision item 1).
- `screening/export.py`: the methods paragraph states each amendment (date, what changed, from, to, reason, how many decided records were screened again) or "The criteria were not changed after the protocol was signed."; the amendments file is a listed source. `console/api/screening.py`: the publish row carries `criteria_amendments_sha256`.
- Refusal codes `CRITERIA_AMENDMENT_INVALID`, `CRITERIA_AMENDMENT_NO_BATCHES`, `CRITERIA_AMENDMENT_AFTER_APPROVAL`, `CRITERIA_SIDE_EMPTY`, `REASON_CODE_RETIRED` in `console/refusals.py` and `docs/architecture/screening-api-contract.md` §7; that contract's §2, §3.1, §3.3, §3.4 and §4 amended; its fixtures (`tests/fixtures/screening_api/`) regenerated, five files gaining additive fields only (`criteria_version`, `recheck`, `since_version`, `shown_again`, `earlier_wording`).

| DoD | Test (`tests/console/test_criteria_amendments_api.py` unless named) | State |
| :-- | :-- | :-- |
| 1 | `test_dod1_a_revision_is_one_line_and_one_journal_row_and_touches_no_bound_artifact` (the protocol, the batch file and every registered artifact hashed before and after; the fingerprint and `protocol_changed` unchanged); `test_dod1_the_routes_are_desktop_only` | done |
| 2 | `tests/unit/test_criteria_readers.py` (every source file naming `screening_criteria` is allow-listed with its reason; the moved readers no longer name it; the MCP record tool reads the context's criteria); `test_dod2_every_reader_takes_the_amended_wording` (record route, intake reason check, the run estimate's prompt, MCP record tool); `test_dod2_the_file_handoff_worker_refuses_once_the_criteria_are_amended`; `test_dod9_an_agent_run_stamps_its_drafts_with_the_version_in_force` (the agent run); agreement and export under DoD 9 and 10 | done |
| 3 | `test_dod3_reword_keeps_the_id_split_and_remove_retire_and_a_number_is_never_reused`; `test_dod3_a_retired_reason_is_refused_on_a_new_decision_and_stays_valid_on_earlier_ones` (the replay stays `duplicate`; `FAILS-` a retired inclusion) | done |
| 4 | `test_dod4_events_and_drafts_carry_the_engine_stamped_version`; `test_dod4_a_version_1_draft_id_is_unchanged_by_m11b` | done |
| 5 | `test_dod5_a_reword_shows_again_include_unclear_and_excludes_citing_it_only`; `test_dod5_an_added_criterion_shows_again_include_and_unclear_but_no_exclude`; `test_dod5_a_reason_category_change_shows_nothing_again`; `test_dod5_a_batch_holding_a_record_shown_again_is_not_fully_decided` (the coverage check refuses); `test_dod5_a_record_shown_again_is_decided_again_by_a_superseding_event`; `test_dod5_a_published_screening_refuses_while_a_record_waits` (collect refuses; no generation) | done |
| 6 | `test_dod6_refused_before_batches_exist`; `test_dod6_refused_after_a_batch_is_approved`; `test_dod6_refused_in_a_later_screening_round`; `test_dod6_invalid_revisions_are_refused_and_write_nothing` (11 cases); `test_dod6_a_retired_id_cannot_be_revised`; `test_dod6_the_dry_call_answers_the_new_ids_and_writes_nothing` | done |
| 7 | `test_dod7_a_revision_that_empties_a_side_is_refused` (recorded and dry) | done |
| 7b | `test_dod7b_the_criteria_route_answers_the_criteria_in_force` | done (engine; the dialog and Triage are part C) |
| 8 | `test_dod8_the_criteria_file_is_rewritten_and_the_earlier_one_backed_up`; `test_dod8_a_journal_failure_takes_every_write_back` | done |
| 9 | `test_dod9_drafts_of_an_earlier_version_are_labelled_and_left_out` (draft read, agreement, setup count); `test_dod9_calibration_and_queue_order_leave_earlier_drafts_out`; `test_dod9_an_agent_run_stamps_its_drafts_with_the_version_in_force` | done (engine; "Draft again" on the run screen is part C) |
| 10 | `test_dod10_the_methods_paragraph_reports_each_amendment_and_the_publish_row_its_digest` (every number traced to a figure); `test_dod10_with_no_amendment_the_paragraph_says_the_criteria_were_not_changed`; `test_dod10_the_publish_journal_row_carries_the_amendments_digest` (through `POST /screening/actions/publish`) | done |
| 21 | the four contract checks before (`2dc2811c`) and after (Evidence) | done for part A |

Fails before: on `origin/main`, `src/scholar_harness/screening/criteria.py` does not exist, so both new test files stop at collection (`ImportError`). In the inner run on the first build commit, `test_screening_api_contract.py::test_the_committed_fixtures_are_what_the_engine_produces` failed until the fixtures were regenerated, and `test_console_refusals.py::test_every_contract_code_is_in_the_console_set` until §7 listed the five codes.

Contract v1: unchanged. No file under the baseline globs is touched. The projected batch decisions files keep their shape (a record shown again is left out, as a record in conflict already is). `criteria_version` lives in the harness event log and `proposals.jsonl` only.

Not verified: no live run and no model call (the agent run is tested with the existing fake driver); the methods sentences' wording is a proposal (record (h)); how many records a real revision shows again and how long the re-check takes (needs the researcher's review); the phone's offline queue across a revision (decision item 5), tested only as the rule it is; the screens (part C).

Review round 1 (`milestone-reviewer`, on `7ce756ef`): **CHANGES**, 1 P2, 5 P3, 2 P4, all taken:

| # | Finding | Repair | Test (fails before: the reviewer's probes on `7ce756ef`) |
| :-- | :-- | :-- | :-- |
| P2-1 | A batch decided through the file hand-off was invisible to an amendment (counted 0, shown again 0) and was then approved under the old wording; the methods paragraph would say no record had been decided | a revision (and its dry call) is refused `CRITERIA_AMENDMENT_HANDOFF` (409) while a current batch holds a worker recommendation or a decisions file not built from events (decision item 10); contract §4 and §7 | `test_review_f1_a_batch_decided_through_the_file_handoff_blocks_a_revision`, `test_review_f1_a_worker_recommendation_alone_blocks_a_revision`, `test_review_f1_event_decided_batches_do_not_block_a_revision` |
| P3-2 | A reword with the same text and another reason category was recorded as a reword and showed records again | a reword must change the text; the refusal points to `op: reason_category` | `test_review_f2_a_reword_that_keeps_the_text_is_refused_and_points_to_reason_category` |
| P3-3 | The DoD 2 guard matched only the quoted key | the scan also matches `.screening_criteria`, `Criteria.from_protocol(` and the agent kit's `criteria_from_protocol(protocol`; `measure.py` and `prompt_gate.py` allow-listed with their reasons; each pattern must find a file | `tests/unit/test_criteria_readers.py::test_each_pattern_finds_a_known_reader` and the widened scan |
| P3-4 | `/agreement` could compare a v1 decision with a v2 draft | a decision is compared only when its version is the version in force (the drafts compared already are) | `test_review_f4_agreement_compares_a_decision_and_a_draft_of_the_same_version_only` |
| P3-5 | A split had no cap (300 texts accepted) | 2 to 10 texts (`MAX_SPLIT_TEXTS`) | `test_review_f5_a_split_takes_at_most_ten_texts` |
| P3-6 | Stale status line, no open-decisions row, a stale line in "What the main session must change" | updated | (none) |
| P4-7 | `validate_event` accepted a retired reason | it refuses `REASON_CODE_RETIRED` (intake still lets a stored event replay as a duplicate) | `test_review_f7_validate_event_refuses_a_retired_reason` |
| P4-8 | A loose assertion on the collect refusal | asserts the refusal names batch 1 and that no projection is stale | `test_dod5_a_published_screening_refuses_while_a_record_waits` |

Follow-ups from round 1, not repaired here: the browser POST allowlist (`console/browser.py`) and the UI proxy list need `api/v1/screening/criteria/amendments` (part C); an MCP draft submitted after a revision is stamped at receipt (the class of decision item 5); a study in conflict at the time of a revision is not counted, and resolving it keeps the earlier outcome under the new version without a recheck; `append_event` writes the journal row before `project.json` (repo-wide pattern); approval does not take the events lock, so a revision and an approval could interleave (read, not run).

Evidence (every Python run with `-n 4`, after the machine stopped on 2026-11-21 with three suites running at once):

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| contract (before) | `2dc2811c` | `generate_contract_baseline.py --check`; `generate_protocol_schema.py --check` | current; in sync | |
| inner | `40668085` (working tree) | `select_test_gate.py --changed origin/main --stage inner`: `pytest tests/console tests/kits/agent` and the screening files, `-m "not slow" -n 4` | 1443 tests: 1439 passed, 1 skipped, 3 failed (the two named above, repaired; `test_draft_store_lock.py::test_a_side_write_in_another_process_does_not_undo_a_save`, Inception's area, passes alone: a load flake) | 533 s |
| targeted | `b5b9dd02` | the two new files, `test_console_refusals.py`, `test_screening_api_contract.py`, `-n 4` | 55 passed | 46 s |
| contract (after) | `0695dd2a` | `generate_contract_baseline.py --check`; `generate_contract_schemas.py --check`; `generate_two_study_contract_fixture.py --check`; `generate_protocol_schema.py --check`; `git diff --check origin/main...HEAD`; both ruff commands; `select_test_gate.py --check`; `sync_skills_bundle.py --check` | current; exit 0; exit 0; in sync; clean; clean; OK; OK | |
| pr | `0695dd2a` | `uv run pytest -q -n 4 --junitxml` (full suite, `--extra dev --extra pdf --extra rag` installed); both ruff commands and the contract checks above | 6112 tests: 6097 passed, 15 skipped, 0 failed, 0 errors (from the `<testsuite>` attributes) | 1042 s |

| targeted (round 1 repairs) | `2e1874f8` (working tree) | the two new files and `test_console_refusals.py`, `-n 4` | 57 passed (after the §7 row for `CRITERIA_AMENDMENT_HANDOFF`) | 33 s |
| pr (final) | `2e1874f8` | `generate_contract_baseline.py --check`; `generate_protocol_schema.py --check`; both ruff commands; `git diff --check origin/main...HEAD`; `uv run pytest -q -n 4 --junitxml` (full suite) | current; in sync; clean; clean; clean; 6120 tests: 6105 passed, 15 skipped, 0 failed, 0 errors | 831 s |

No UI file changed in part A (`git diff origin/main...HEAD -- apps` is empty), so typecheck, vitest, build and Playwright were not run.

Review round 2 (on `6fa05b7e`): **APPROVE**. The eight round-1 repairs confirmed (the reviewer's hand-off probe is now refused `CRITERIA_AMENDMENT_HANDOFF`); 294 targeted tests, 0 failed (`-n 4`); contract checks current; no regression found. Two P3 points, not blocking, left for the start of part C (they shape the revise dialog):
- `GET /screening/criteria` answers `can_amend: true` while every revision would be refused `CRITERIA_AMENDMENT_HANDOFF`; it should add `not handoff_batches(...)` and name the batches, so the dialog is not offered and then refused.
- The `CRITERIA_AMENDMENT_HANDOFF` message says to decide the batches in Triage first, but a worker recommendation file stays and keeps the refusal; the message (and the §7 row) should not promise that way out, or a way to clear a hand-off batch should be defined.

~~**Part A: READY FOR PR**~~ (superseded below: item 5 changed on 2026-11-21; not pushed). Branch `dev/m11b/part-a-criteria-in-force`. The PR gate on `2e1874f8` stands for the later commits, which change this record only.

#### Part A, after the researcher's answers (2026-11-21)

The researcher accepted items 1 to 4 and 6 to 10 as built and decided item 5 as **"bind the version"** (decision entry, item 5). Part A went back to IN PROGRESS for it.

What changed:
- `GET /records/{id}` hands out `binding.criteria_version`; `events._criteria_refusal` refuses a new event bound under another version with `STALE_BINDING`, naming both versions. A binding without the field reads as version 1. Not in `is_current`, so stored decisions keep counting and a stored event replays as a `duplicate`. The projected batch decisions file keeps its own binding (unchanged).
- `tests/test_screening_events.py` builds its events with the binding the record route hands out (`criteria_version`).
- Contract §3.1 amended; the fixtures regenerated: the event bindings in nine fixture files gain `"criteria_version": 1` (additive).
- The desktop Triage already echoes the record's `binding` object unchanged and shows `STALE_BINDING` as its stale state, so no UI change is needed for it to work; the TypeScript `Binding` type gains the field in part C. There is no phone client in this repository (no offline queue in `apps/research-ui`); the engine answers a refused result per event, never drops it, which is what a phone flush must show.

| Item 5 | Test (`tests/console/test_criteria_amendments_api.py`) | Fails before (on `f1968ccd`) |
| :-- | :-- | :-- |
| the binding names the version | `test_item5_the_record_binding_names_the_criteria_version` | yes |
| a decision bound under version 1, received after a revision, is refused `STALE_BINDING`; nothing stored; the record stays in `needs_you`; decided again it is accepted as version 2 | `test_item5_a_decision_bound_under_the_earlier_wording_is_refused_and_the_record_stays_queued` | yes (it was accepted and stamped 2) |
| a binding without the field is version 1 | `test_item5_a_binding_without_a_version_reads_as_version_1` | yes |
| a stored event replays as `duplicate` and still counts | `test_item5_a_stored_event_replays_as_a_duplicate_and_still_counts_after_a_revision` | no (already held; kept as a guard) |

Pilot decisions (part B) carry no binding, so this change does not reach them; see part B's decision entry.

Evidence for the item 5 change (`-n 4`):

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| targeted | `c100e314` (working tree) | the item 5 tests first on `f1968ccd`'s code: 3 of 4 failed as expected; then `test_criteria_amendments_api.py`, `test_screening_events.py`, `test_screening_api_v1.py`, `test_screening_api_contract.py` | 155 tests, 1 failed (the committed fixtures, regenerated: additive `criteria_version` in nine event bindings); then 62 passed | 62 s; 52 s |
| pr | `c100e314` | contract baseline, protocol schema, contract schemas, two-study fixture; both ruff commands; `git diff --check origin/main...HEAD`; `uv run pytest -q -n 4 --junitxml` (full suite) | current; in sync; exit 0; exit 0; clean; clean; one finding (a blank line at the end of this record, fixed in the next commit, documents only); 6124 tests: 6109 passed, 15 skipped, 0 failed, 0 errors | 558 s |

Review round 3 (on `bb32cd80`, the item 5 delta): **CHANGES**, 1 P2 and 1 P4, both taken:

| # | Finding | Repair | Test (fails before: on `bb32cd80`) |
| :-- | :-- | :-- | :-- |
| P2-1 | After any revision, a conflict from before it could not be resolved in the app: the resolve route copied the kept event's binding (version 1), which item 5 refuses, so its batch stayed blocked | the resolution is bound to the record as it is now and stamped with the criteria version of the decision it keeps (decision item 11, PROPOSED); a revision that could change it shows the record again; contract §4 resolve row | `test_round3_a_conflict_resolved_after_a_wording_change_is_shown_again`, `test_round3_a_conflict_resolved_after_a_category_change_counts`, `test_round3_keeping_an_exclusion_whose_criterion_was_retired_resolves_and_is_shown_again` |
| P4-2 | `binding.criteria_version: true` (or `1.0`) read as version 1 | the bound version must be an int (not a bool); anything else is `STALE_BINDING` | `test_round3_a_bound_version_must_be_an_integer` |

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| targeted | `58ce7bd7` (working tree) | the four round-3 tests first on `bb32cd80`: 4 of 4 failed; then `test_criteria_amendments_api.py`, `test_screening_api_v1.py`, `test_screening_events.py`, `test_screening_api_contract.py` | 159 passed | 46 s |
| pr | `58ce7bd7` | contract baseline, protocol schema, contract schemas, two-study fixture; `ruff check scripts/` and the `src/` real-bug set; `git diff --check origin/main...HEAD`; `uv run pytest -q -n 4 --junitxml` (full suite) | current; in sync; exit 0; exit 0; clean; clean; clean; 6128 tests: 6113 passed, 15 skipped, 0 failed, 0 errors | 648 s |

Review round 4 (on `0a47f3b3`): **APPROVE**. Both round-3 repairs confirmed; the intake parameter is reachable only from the engine's resolve route (a client field is refused); its stamp and retired-reason exemption apply only there, and a retired id kept by a resolution is always shown again; conflicts without a revision behave as before; 199 targeted tests, 0 failed. Follow-ups carried to part C: read a decision's `criteria_version` (not its binding) to label it; `can_amend` and the `CRITERIA_AMENDMENT_HANDOFF` message (round 2); the round-1 list.

**Part A: READY FOR PR** (not pushed). Branch `dev/m11b/part-a-criteria-in-force`. The PR gate on `58ce7bd7` (6128 tests, 0 failed) stands for the later commits, which change this record only. Decision item 11 was accepted by the researcher on 2026-11-21, as built, and the push was approved the same day.


### Part B: the pilot

Branch `dev/m11b/part-b-pilot`, stacked on part A (`f1968ccd`), with `origin/main` merged (`62bac271`, M11a part D) · Lane **RELEASE** (as declared: public routes, a second decision intake, persisted records, an additive field on a public answer) · Decisions: `docs/decisions.md` "2026-11-21 — M11b part B: the pilot, the build's choices" items 1 to 10 (PROPOSED). The researcher's answers bind it: pilot decisions are not counted and the records are screened again (5); the checklist stays collapsed (6); the agent check on the pilot with an explicit model (9); counts only, never one record's draft (11).

What was built:
- `src/scholar_harness/screening/pilot.py`: the draw (records with no main decision and in no earlier pilot, in snapshot order, `random.Random(seed).sample` with a seed the engine draws and records; the dry call); the pilot decisions file `pilot_NNN_decisions.jsonl` and its intake (the event intake's reason and input checks; `PLD-` ids derived from the client's `event_id`; engine-stamped `received_at`, `criteria_version`, `protocol_fingerprint`; one journal row per request, counts only); the end of a pilot (`pilot_NNN_closed.json`, by "End the pilot" or when the last record is decided; `SCREENING_PILOT_CLOSED`); the result, recomputed when read: counts per outcome, per criterion the exclusions it was the reason for, the checklist's and the drafts' `not_reported`, "read differently" against the checklist answers or what a decision implies, the seven readings of (f) as fixed rules with their counts, the readings not computed with what they need, and the previous pilot beside it. All writes run under the events lock.
- `screening/events.py`: a new main decision on a record of the open pilot is refused `PILOT_OPEN` (new events only; the open pilot's records are re-read under the lock).
- `console/api/screening_v1.py`: `POST /screening/pilot`, `POST /screening/pilot/{id}/decisions`, `POST /screening/pilot/{id}/close`, `GET /screening/pilot/{id}/result` (desktop only); `/summary` gains `pilot`; `GET /queue?view=pilot` (drawn order, `checklist_default: "collapsed"`), and the open pilot's records leave the other views; `POST /proposals/calibrations` takes an additive `pilot_id` (labels from the pilot file); `/agreement`'s `splits_by_criterion` rows gain `answered_by_both`; a revision made during a pilot records its `pilot_id`.
- `screening/agent_runs.py`: a run records `pilot_id`; its drafts carry it; the calibration score reads the pilot's labels, comparing a draft only with a pilot decision of the same criteria version.
- `screening/export.py`: the methods paragraph states the pilots (records decided, seed, the corpus size) and that their decisions were not counted; an amendment with no counted decision says it was made during or after the pilot.
- Refusal codes `PILOT_OPEN`, `PILOT_RECORD_UNKNOWN`, `PILOT_CLOSED`, `PILOT_NOT_FOUND`, `PILOT_SIZE_INVALID` in `console/refusals.py` and `screening-api-contract.md` §7; §3.4 and §4 amended; the fixtures regenerated (`/summary` gains `"pilot": null`, two files, additive only).

| DoD | Test (`tests/console/test_criteria_pilot_api.py` unless named) | State |
| :-- | :-- | :-- |
| 11 | `test_dod11_the_dry_call_answers_n_the_pool_and_the_time_and_writes_nothing`; `test_dod11_a_draw_writes_the_file_and_one_journal_row`; `test_dod11_the_same_seed_on_the_same_snapshot_gives_the_same_list`; `test_dod11_records_with_a_main_decision_or_in_an_earlier_pilot_are_not_drawn`; `test_dod11_a_size_outside_20_to_100_in_tens_is_refused`; `test_dod11_more_than_the_records_left_is_refused`; `test_dod11_refused_before_batches_after_approval_and_while_a_pilot_is_open`; `test_dod11_the_pilot_routes_are_desktop_only` | done |
| 11b | `test_dod11b_the_summary_names_the_open_or_last_pilot` | done |
| 11c | `test_dod11c_a_pilot_decision_is_a_line_of_its_own_file_with_engine_fields`; `test_dod11c_the_event_intakes_checks_apply` (9 cases); `test_dod11c_a_retired_reason_is_refused_in_the_pilot`; `test_dod11c_a_record_outside_the_pilot_and_an_unknown_pilot_are_refused`; `test_dod11c_pilot_decisions_reach_no_counted_reader` (0 decided, no event, no batch decisions file, empty decided view and agreement, an empty PRISMA preview, collect refuses) | done |
| 11d | `test_dod11d_a_main_decision_on_an_open_pilot_record_is_refused`; `test_dod11d_ending_the_pilot_returns_its_records_blind_to_the_pilot_decision` (queue and record carry nothing of the pilot; the main decision is accepted, no conflict); `test_dod11d_a_pilot_closes_by_itself_when_its_last_record_is_decided` | done |
| 12 | `test_dod12_the_pilot_view_lists_the_drawn_records_in_drawn_order`; `test_dod12_the_pilot_view_is_empty_without_a_pilot` | done (engine; Triage is part C) |
| 13 | `test_dod13_from_the_decisions_alone_three_readings_and_the_four_it_could_not_compute`; `test_dod13_with_the_agent_check_the_mirror_and_the_unreadable_criterion_show` (and no per-record draft in the answer); `test_dod13_read_differently_against_checklist_answers`; `test_dod13_a_second_pilot_has_the_first_beside_it`; `test_dod13_a_revision_during_the_pilot_labels_the_versions_and_shows_nothing_again` | done |
| 14 | `test_dod14_the_agent_check_on_a_pilot_reads_its_labels_from_the_pilot_file` (explicit model, the fake driver, labels and drafts, the refusals; the route without `pilot_id` is unchanged, its own tests pass) | done (engine; the UI test that the body always has a model is part C) |
| 15 | `test_dod15_splits_by_criterion_carry_answered_by_both` | done |
| (h) | `test_methods_state_the_pilot_and_that_its_decisions_were_not_counted` (every number traced to a figure; the amendment during the pilot) | done |
| 21 | the contract checks before and after (Evidence) | done for part B |

Fails before: on part A's head `f1968ccd`, `screening/pilot.py` does not exist and the routes answer 404/405, so `tests/console/test_criteria_pilot_api.py` stops at collection (`ImportError`).

Contract v1: unchanged. Pilot decisions are not decision events and are never handed to the Contract v1 collector; the projected batch decisions files are untouched by a pilot (tested); no file under the baseline globs changes.

Not verified: no live run and no model call (the agent check runs on the fake driver); whether the observation thresholds and the minimum counts (decision item 4) are useful on a real pilot (DoD 22, the researcher's own pilot); the screens (part C).

Evidence (Python runs with `-n 4`):

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| targeted | `24e69596` | the new file with `test_console_refusals.py`, `test_screening_api_contract.py`, part A's two files | 101 tests, 0 failed (after the §7 rows for the five codes) | 51 s |
| targeted | `ada92bc1` (working tree) | `tests/console/test_criteria_pilot_api.py` | 38 passed | 35 s |
| pr | `ada92bc1` | `generate_contract_baseline.py --check`; `generate_protocol_schema.py --check`; `generate_contract_schemas.py --check`; `generate_two_study_contract_fixture.py --check`; both ruff commands; `git diff --check origin/main...HEAD`; `uv run pytest -q -n 4 --junitxml` (full suite) | current; in sync; exit 0; exit 0; clean; clean; clean; 6176 tests: 6161 passed, 15 skipped, 0 failed, 0 errors | 691 s |

The commit after `ada92bc1` (`68e1e783`) is this record only. No UI file changed (`git diff origin/main...HEAD -- apps` is empty), so the UI gates were not run.

Review round 1 of part B (`milestone-reviewer`, on `36de9009`): **CHANGES**, 1 P2, 6 P3, 5 P4, all taken (on `fc90db07`, after part A's item 5 and round 3/4 were merged in):

| # | Finding | Repair | Test (`tests/console/test_criteria_pilot_api.py`; fails before: the reviewer's probes on `36de9009`) |
| :-- | :-- | :-- | :-- |
| P2-1 | The agent check on a pilot answered `missed_includes` with the ids of pilot records, undecided in the main screening (answer 11; contract §4) | with `pilot_id` the list is always empty; `missed_includes_count` gives the number (also for the main calibration) | `test_review_f1_the_agent_check_on_a_pilot_names_no_record`, `test_review_f1_a_main_calibration_still_names_its_missed_records` |
| P3-2 | The methods paragraph could say "piloted on 0 records" | a pilot with no decision is left out | `test_review_f2_a_pilot_with_no_decision_is_not_in_the_methods` |
| P3-3 | `splits_by_criterion` gained rows with `n: 0`, so today's Agreement screen showed zero bars | split rows stay real splits, each with `answered_by_both`; a new top-level `answered_by_both` lists every criterion | `test_dod15_splits_by_criterion_carry_answered_by_both`, `test_review_f3_old_clients_see_no_zero_split` |
| P3-4 | Readings below their minimum vanished silently | named in `not_computed` with `have` and `min` | `test_review_f4_readings_below_their_minimum_are_named` |
| P3-5 | "Never used" took its full form for a criterion nobody answered | full form only for an answered criterion | `test_review_f5_never_used_takes_its_full_form_only_for_an_answered_criterion` |
| P3-6 | The draw ignored records decided through the file hand-off | the draw is refused `CRITERIA_AMENDMENT_HANDOFF` (decision item 13) | `test_review_f6_a_draw_is_refused_while_a_batch_was_decided_through_the_handoff` |
| P3-7 | A second pilot decision without `supersedes` silently won | refused `INVALID_OUTPUT` (decision item 12) | `test_review_f7_a_second_pilot_decision_must_supersede_the_first` |
| P4-8 | A catch-all assertion; "nothing approvable" not exercised | the collect refusal is asserted by message; the coverage check refuses each batch | `test_dod11c_pilot_decisions_reach_no_counted_reader` |
| P4-9 | `study_ids` became optional without `pilot_id` (422 `BODY_INVALID` became `INVALID_OUTPUT`) | required again unless `pilot_id` is given (a model validator) | `test_dod14_the_agent_check_on_a_pilot_reads_its_labels_from_the_pilot_file` |
| P4-10 | `view=pilot` answered phone tokens | refused `TOKEN_SCOPE_REFUSED` | `test_review_f10_the_pilot_view_is_desktop_only` |
| P4-11 | "1 records"; three pilots read badly; "after the first revision" not built | wording fixed; a later pilot drawn after a revision says so | `test_review_f11_the_pilot_sentence_reads_well_for_one_record_and_three_pilots` |
| P4-12 | A blank line at the end of this record | removed | (`git diff --check`) |

Follow-ups taken: the open pilot's id is read under the events lock when a revision is recorded (`test_followup_a_revision_records_the_pilot_open_at_that_moment`); a pilot number is never reused, even when a draw file is unreadable (`test_followup_a_pilot_number_is_never_reused_even_if_a_draw_file_is_unreadable`); `/summary` computes the recheck count once. Not taken: another batch can be approved while a pilot is open (the pilot result's revise would then be refused; the screen in part C shows the fixed state).

Part A's item 5 ("bind the version") does not reach pilot decisions: they carry no binding and are labelled with the version in force when received (decision item 11, PROPOSED, with the binding alternative).

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| targeted | `3a92daa2` (working tree) | `tests/console/test_criteria_pilot_api.py` with the new review tests; part A's file, `test_agent_runs_api.py`, `test_screening_drafts_api.py` | 50 passed; 132 tests, 0 failed after the agreement test took the new shape | 55 s; 63 s |
| pr (round 1 repairs) | `fbf8887d` (part A's `c65a48f2` and `origin/main` `b36303b8` merged in) | contract baseline, protocol schema, contract schemas, two-study fixture; both ruff commands; `git diff --check origin/main...HEAD`; `uv run pytest -q -n 4 --junitxml` (full suite) | current; in sync; exit 0; exit 0; clean; clean; clean; 6219 tests: 6204 passed, 15 skipped, 0 failed, 0 errors | 689 s |

A gate started on `3a92daa2` was stopped when part A's branch moved (it brought code from `origin/main`); the run above is on the merged head.

Review round 2 of part B (on `0cdf80aa`): **APPROVE**. The twelve round-1 repairs and the three follow-ups confirmed by the reviewer's probes (11 probes, 366 targeted tests, 0 failed, `-n 4`); the merges of part A and `origin/main` did not break part B (in `_criteria_refusal`, `PILOT_OPEN`, then the retired reason with `resolution_version`, then the bound version, all on new events only); decision items 11 to 13 match the code. One P4, taken (documents only): the `GET /agreement` shape in contract §4 lists the new top-level `answered_by_both`.

**Part B: READY FOR PR** (not pushed). Branch `dev/m11b/part-b-pilot`, stacked on part A. The PR gate on `fbf8887d` (6219 tests, 0 failed) stands for the later commits, which change documents only. Decision items 1 to 13 of part B wait for the researcher.

Part B's decision items 1 to 13 were accepted by the researcher on 2026-11-21 (main session), and the push of part B was approved; the main session pushes it.

### Part C: the screening screens

Branch `dev/m11b/part-c-screens`, stacked on part B (PR 277 head `ea260382` merged in, and `origin/main` `64fd8212`, M12a part A) · Lane **RELEASE** (re-declared after review round 1, finding 1: the public queue answer gains `shown_again`, `pilot_decision` and a new order of "Needs you"; `GET /criteria` changes `can_amend` and gains `handoff_batches`; the browser POST allowlist widens; a refusal message changes. Closure evidence is the CI matrix on the PR, which only the push can run) · Spec `docs/ux/phase2-screening/final/13-criteria-pilot.md` FINAL (2026-11-21, questions 5 to 8 answered by the researcher) · Decisions: `docs/decisions.md` "2026-11-22 — M11b part C" items 1 to 17 (accepted by the researcher 2026-11-22) · Status: **READY FOR PR** (review round 2 APPROVE; not pushed).

The engine side (the follow-ups the part A and B reviews left for part C):
- The browser may POST to `api/v1/screening/criteria/amendments`, `api/v1/screening/pilot` and `api/v1/screening/pilot/pilot_NNN/(decisions|close)` (`console/browser.py` and the development proxy `route.ts`, kept equal).
- `GET /screening/criteria` answers `can_amend: false` and `handoff_batches` while a batch was decided through the file hand-off, so the revise dialog is not offered and then refused.
- The `CRITERIA_AMENDMENT_HANDOFF` message names the only way to revised criteria (a new screening from this protocol) instead of suggesting Triage, which does not clear a worker recommendation; contract §7.

| Item | Test | Result (`-n 4`) |
| :-- | :-- | :-- |
| the POST allowlist | `tests/console/test_criteria_pilot_plumbing.py::test_the_browser_may_post_to_the_new_routes_only` (7 cases); `test_browser_access.py` (parity with `route.ts`); `vitest related route.ts` | 77 Python tests passed with part A's file; vitest 69 passed; `tsc` clean |
| `can_amend` and `handoff_batches` | `test_the_criteria_route_offers_no_revision_while_a_handoff_batch_exists` | passed (fails on `5d13e86c`: `can_amend` true, no `handoff_batches`) |
| the refusal's wording | `test_the_handoff_refusal_names_the_only_way_to_revised_criteria` | passed (fails on `5d13e86c`: the message names Triage) |

The UI dependencies of this worktree were installed with `npm ci --offline` from the local cache (no network).

The screens:
- Engine, additive (decision items 1 and 2; screening API contract §4): "Needs you" lists the records shown again first and every queue item carries `shown_again`; the items of `view=pilot` carry `pilot_decision`; `_pilot_queue` reads the pilot decisions' heads.
- `lib/screening-v1.ts`: the types and calls for the criteria in force, revisions, the pilot (draw, decisions, close, result), the queue's new fields and views, `RecordDetail.shown_again`, the calibration's `pilot_id` and `missed_includes_count`, `answered_by_both`.
- Prepare (state A): `components/screening-pilot-card.tsx`, the card before, during and after a pilot, with the draw's dry call and its confirmation, the records shown again, the fixed state after an approval.
- Triage (state B; `components/triage-page.tsx`, `lib/triage-copy.ts`): `?view=` opens a view; the pilot view posts to the pilot route (never to `/decisions/events`), shows the banner, "Pilot record k of n", your pilot decision with Next and Change, and the pilot's hand-off; a record shown again has the earlier-decision card, the "Shown again" tag and the revision banner with "What changed", and is decided again by superseding the decision shown; `PILOT_OPEN` links to the pilot; `REASON_CODE_RETIRED` reads the criteria again. The new refusal codes have their state copy (`lib/screening-states.ts`).
- The result (state C) and the revise dialog (state D): `app/[locale]/screening/pilot/page.tsx`, `components/screening-pilot.tsx`, `components/screening-pilot-copy.ts` (en, fr, ar): counts with denominators, the per-criterion table (checklist and agent columns only when the answer has them, draft-styled, the comparison with the previous pilot), the readings with one "Revise {id}" per id, the "not computed" line with the estimate, the readings below their minimum, the records list (filters by criterion and outcome, 25 a page, a read-only record), the small-sample sentence, the action bar, the details column; the end dialog, the revise dialog (operation, fields, reason of at most 500 characters, dry call, confirmation, record), the agent-check dialog (model, count, estimate, data flow, ceiling, `pilot_id` and `model` always sent, progress, cancel, "Missed includes" as a count).
- The run screen: "Draft again the {n} records whose draft predates the revision" (decision item 15).
- The guidance audit gains row S-PL1 for the result's one hint (`docs/ux/shared/final/03-guidance.md`; the audit fixture reads the pilot's catalog for `S-PL` rows).

| DoD | Test | State |
| :-- | :-- | :-- |
| 16 Prepare | `tests/screening-pilot-card.test.tsx` (8: draw only after the confirmation, its words, a refused draw, in progress, ended with records shown again, fixed after approval, hidden before batches, copy parity) | done |
| 16 Triage | `tests/triage-pilot.test.tsx` (10: `?view=pilot`, banner and position, the pilot route only, a change of mind supersedes, an ended pilot cannot be changed, the pilot hand-off, the shown-again banner, tag and earlier card, deciding again supersedes, `PILOT_OPEN` link, `REASON_CODE_RETIRED` reads again, the pilot view offered only while open); the existing `tests/triage.test.tsx` unchanged | done |
| 16 result | `tests/screening-pilot.test.tsx` (20: counts and denominators, absent columns, draft-styled agent columns and their source, an open pilot, the "not computed" line, observations, nothing stood out, the records list, the end dialog, the revise dialog and its refusal, the agent-check dialog with its model rules, consent and key, the fixed state, an unknown pilot, a second pilot, copy parity) | done |
| 16 axe light and dark | `tests-browser/screening-pilot.spec.ts` (both projects): the keyboard pilot to its result, the result at 1440 and 1280 px with a revision, the end dialog, Triage with a record shown again; axe on each | done (10 passed) |
| 17 | `criteria.revise-dialog` cases in `tests/screening-pilot.test.tsx`; the browser flow in `tests-browser/screening-pilot.spec.ts` | done |
| 14 (UI half) | `pilot.calibration-dialog` cases: the body always carries `model` and `pilot_id`; Haiku without a last model | done |
| 9 (UI half) | `tests/screening-proposals.test.tsx` "proposals.redraft" (2) | done |

Fails before: on part B's head the pilot result route `/screening/pilot` does not exist, Triage has no pilot view, and `tests/triage-pilot.test.tsx`, `tests/screening-pilot.test.tsx` and `tests/screening-pilot-card.test.tsx` fail at import (the components are new).

Contract v1: unchanged (`generate_contract_baseline.py --check` current). The two queue fields are additive to the screening API (contract §4 notes), not Contract v1.

Not verified: no live engine and no real browser session with a real workspace (the browser tests answer the console proxy with a fake of the engine's shapes); no model call (the agent check is tested against a fake run); the phone (desktop only, answer 8); wording and layout stay open until the researcher sees the built screens (spec 13). Decision items 1 to 17 wait for the researcher.

Evidence (part C; Python with `-n 4`, one heavy job at a time):

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| targeted | `8c7ed969` (working tree) | `vitest run tests/triage-pilot.test.tsx`, `tests/screening-pilot.test.tsx`, `tests/screening-proposals.test.tsx`; `tsc` | 9, 20, 20 passed; clean | |
| checkpoint | `91e5da93` | full `vitest run` | 1153 passed, 3 failed: the details rule and the hint audit on the new page (repaired in `e994b7fd`, row S-PL1), and an inception proposals test that passed when run again | 198 s |
| targeted | `ec7f2a98` | `playwright test tests-browser/screening-pilot.spec.ts` (port 3127; 3117 was held by another process) | 10 passed (chromium and chromium-dark) after the revise dialog's fields were located by element | 60 s |
| pr | `ec7f2a98` | `uv run pytest -q -n 4 --junitxml` (full suite) | 6268 tests: 6253 passed, 15 skipped, 0 failed, 0 errors | 996 s |
| pr | `ec7f2a98` | both ruff commands; `generate_contract_baseline.py --check`; `generate_protocol_schema.py --check`; `generate_contract_schemas.py --check`; `generate_two_study_contract_fixture.py --check`; `git diff --check origin/main...HEAD` | exit 0; current; in sync; exit 0; exit 0; one blank line at the end of this record (removed in the next commit) | |
| pr | `ec7f2a98` | `npm run typecheck`; `vitest run` (full); `npm run test:browser` (build, then the full browser suite, port 3127) | clean; 82 files, 1157 passed; 674 passed, 12 skipped, 0 failed | 137 s; 921 s |

The browser run rewrote four committed screenshots of screens part C does not touch (workspaces, import, the phone menu); they were restored, not committed.

Review round 1 of part C (`milestone-reviewer`, on `7c9e3311`): **CHANGES**, 2 P2, 6 P3, all taken. The reviewer confirmed: pilot decisions never reach `/decisions/events`; answer 11 holds (`pilot_decision` on `view=pilot` only, the agent as counts only, "Missed includes" a count); the calibration body always carries `model` and `pilot_id`; a record shown again supersedes the decision shown; the revise dialog's body is right for the six operations against `plan_amendment`; no Contract v1 change; decision items 1 to 16 match the code.

| # | Finding | Repair | Test (fails before: 9 of these on the components of `7c9e3311`, run with the new tests) |
| :-- | :-- | :-- | :-- |
| P2-1 | The lane was STANDARD although part C changes the public queue answer, `GET /criteria`, the browser allowlist and a refusal message | re-declared **RELEASE**; the closure evidence is the CI matrix on the PR | (record) |
| P2-2 | Dialog focus did not meet spec 13: no trap, the agent-check dialog took no focus, the revise dialog dropped focus to the page on its confirmation and on Back, the draw confirmation did not give focus back | the result's dialog moves focus inside (a control that asks for it, else its heading), keeps Tab inside, and the caller gives it back; the draw confirmation gives focus back to the draw button; after "End the pilot" focus goes to the new heading | `review C round 1` > `finding 2` in `tests/screening-pilot.test.tsx` (2) and `tests/screening-pilot-card.test.tsx` (1) |
| P3-3 | An addition read "… 0 Exclude citing ." | a sentence without a cited criterion (`rev.shownUncited`, en, fr, ar) | `finding 3: an addition that shows records again cites no criterion` |
| P3-4 | With hand-off batches and no approval, the result said "a batch is already approved" and Prepare's card still offered a draw | both show the `CRITERIA_AMENDMENT_HANDOFF` sentence; the card offers no draw | `finding 4` in both files |
| P3-5 | The size field took its step on every keystroke | it keeps what is typed and takes its step when it loses focus or draws | `finding 5: the size field keeps what is typed…` |
| P3-6 | Triage counted the pilot's progress from the queue | the banner and the hand-off read `/summary`'s `pilot` block | `finding 6: the banner shows the engine's pilot counts…` |
| P3-7 | Prepare had two brand buttons once batches existed | Prepare's own button is secondary once batches exist (decision item 17, PROPOSED) | `prepare with batches … has one brand action` |
| P3-8 | Only reword's request body was tested | one test per operation; only a reason-category change sends `reason_category` | `finding 8` (6 tests; they pass before too: the code was already right) |

Follow-ups taken: the earlier-decision card is a labelled region; "Draft again" names the engine's count; spec 13's line on its questions says 8 was answered against its recommendation. Not taken (P4, listed for later): the pilot agent check sends no `base_url`, so a last run on an OpenAI-compatible endpoint would be refused; "1 records are shown again" (a plural); `pilot.saved` names the position of the record just decided; `Ctrl+Enter` does nothing while a dialog is open; an emptied reason category leaves the confirmation's "After" cell empty.

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| targeted | working tree after the repairs | `vitest run` of the pilot result, the pilot card, Triage's pilot file and Prepare; `tsc` | 70 passed (9 of the new ones fail with the components of `7c9e3311`); clean | 40 s |
| pr (round 1 repairs) | `02848caa` | `npm run typecheck`; `vitest run` (full); `npm run test:browser` (build, then the full browser suite, port 3127); the Python suite of `ec7f2a98` stands (no file under `src/`, `tests/` or `scripts/` changed since) | clean; 82 files, 1172 passed; 674 passed, 12 skipped, 0 failed (four unrelated screenshots rewritten again and restored) | 148 s; 998 s |

Review round 2 of part C (on `f6d26718`): **APPROVE** (lane RELEASE confirmed). The eight repairs confirmed with their tests (90 tests of the five repaired files passed at head). One P3, taken: the agent-check dialog left focus on the page once the run view replaced the form; focus now moves into the run view, to Cancel while it runs (`pilot.calibration-dialog` test asserts it). One P4, taken: the record names decision items 1 to 17. Noted, not changed: if `/summary` fails at boot, the pilot banner reads "0 of 0" (the counts are the engine's only); `pilot.saved` stays with the parked P4s.

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| pr (round 2 repair) | `07fbb270` | `tsc`; `vitest run` (full); `playwright test tests-browser/screening-pilot.spec.ts` (both projects, port 3127); the full browser run of `02848caa` stands for the rest (this commit changes one dialog's focus and one test) | clean; 82 files, 1172 passed; 10 passed | 150 s; 78 s |

**Part C: READY FOR PR** (not pushed). Branch `dev/m11b/part-c-screens`, head after this commit. Lane RELEASE: the CI matrix on the PR is the closure evidence and is recorded after the push. Decision items 1 to 17 of part C were accepted by the researcher on 2026-11-22 as built (items 3, 10 and 16 asked one by one, the other fourteen together), and the push was approved.

### Part D: Inception step 5

Branch `dev/m11b/part-d-step5`, stacked on part C (its reviewed head `daaeaa92` merged in, and `origin/main` `55755bd7`: part B as PR 277 and the PDF resolver fix PR 278) · Lane **RELEASE** (the inception draft API, the intent packet and the protocol genesis writes change; new check ids in a public preview) · Decisions: `docs/decisions.md` "2026-11-21 — M11b part D" items 1 to 10 (PROPOSED). Status: **IN PROGRESS** (item 5 changed by the researcher on 2026-11-22; the change, its gate and the review of the delta below).

What was built (engine):
- `inception/steps.py`: the draft fields `method_blinding` (pre-selected "after you decide") and `method_not_reported` (no default); `method_choice`, `method_options` on `steps/criteria`; `build_intent` refuses `METHOD_RULE_UNCHOSEN` (preview and genesis) and writes `method` into the intent; `keep_method_choice` on every save (omitted fields kept; `null` after a choice is `DRAFT_INVALID`). `inception/drafts.py`: a new draft stores the rule unchosen.
- `scholar_protocol/intent.py` and `compiler.py`: `IntentPacket.method` (optional), copied into the protocol's `method` block; `inception/genesis.py` still states the playbook's guideline.
- `inception/importer.py`: a protocol's or an intent's `method` block fills the two questions.
- `inception/checks.py` and the new `inception/criteria_wording.py`: `METHOD_RULE_UNCHOSEN` (blocker) and the five wording checks of (f) plus `CRITERIA_WORDING_NOT_CHECKED` (note), never blockers, each instance its own subject.
- `inception/wizard.py` and `cli.py`: the terminal wizard asks the rule with no default; `--not-reported` on `inception` and `init`; a scripted run without it is refused before anything is written.
- `console/refusals.py` and `screening-api-contract.md` §7: `METHOD_RULE_UNCHOSEN`. `docs/ux/shared/final/02-checks.md`: the seven catalogue and copy rows (engine wording; the screen's copy is part D's UI work).
- Existing tests: the 24 scripted `run_wizard` calls give `not_reported="unclear"` (a question would shift their answers); the shared complete drafts of the inception and MCP-assistant tests carry `method_not_reported`.

| DoD | Test | State |
| :-- | :-- | :-- |
| 18 (engine) | `tests/inception/test_method_questions.py`: `test_a_new_draft_stores_the_rule_unchosen_and_visibility_after_you_decide`, `test_the_two_fields_round_trip_and_a_value_outside_the_enums_is_refused`, `test_a_chosen_rule_cannot_be_unset_and_a_save_without_the_field_keeps_it`, `test_the_unchosen_rule_blocks_step_5_review_and_genesis_and_nothing_is_written`, `test_a_draft_from_before_the_question_says_so`, `test_genesis_writes_the_choice_into_the_method_block_and_the_preview_lists_it`, `test_the_criteria_step_answers_the_options_in_the_engines_order`, `test_an_imported_protocol_with_a_method_block_fills_the_two_questions`, `test_the_assistant_has_no_proposal_kind_for_the_rule` | done (engine; the radios are UI) |
| 18b | `tests/inception/test_method_questions.py`: `test_a_search_amendment_of_a_review_that_chose_decisive_first_is_not_refused`, `test_without_the_method_in_the_intent_the_same_amendment_is_refused` (the failure it prevents), `test_a_protocol_without_the_choice_keeps_its_fingerprint` | done |
| 18c | `tests/inception/test_method_questions.py`: `test_the_wizard_asks_the_rule_with_no_default_until_one_is_chosen`, `test_a_scripted_run_without_the_rule_is_refused_before_anything_is_written`, `test_the_cli_names_the_option`, `test_the_wizard_writes_the_rule_into_the_intent` | done |
| 19 (engine) | `tests/inception/test_criteria_wording_checks.py` (16 tests: each rule at and below its constant, accepted criteria only, never a blocker, a subject per instance, a changed text a new subject, the other-language note, and the honesty fixture: the 2026-11-20 mirror and the contradiction of meaning are not caught) | done (engine; the panel's copy is UI) |
| 18 (screen) | `apps/research-ui/tests/inception-criteria-block.test.tsx` "inception.how-you-will-screen" (5: both questions with the engine's options, visibility pre-selected, the rule with none and no "recommended", the measured figures; the engine's order followed; Continue held and named while unchosen, a choice frees it and the save carries both values; a draft from before the question; the visibility question never holds Continue) and "review.how-you-will-screen" (2); `tests-browser/inception-criteria-block.spec.ts` (the choice through to Review, by keyboard) | done |
| 19 (screen) | `inception-criteria-block.test.tsx` "inception.criteria-checks copy" (the seven ids' sentence, why and action in en, fr and ar); `tests/checks-panel.test.tsx` (the catalogue now 59 ids); the engine's rows are drawn by the existing checks panel | done |
| 20 | `inception-criteria-block.test.tsx` "inception.criteria-block" (4: the header's written line or "Decide every criterion first.", the limits line, the out-of-scope question here with its separators, Shape's one line); `tests-browser/inception-criteria-block.spec.ts` (out-of-scope rows, no sideways scroll at 375, 1024, 1280 and 1440 px, Arabic, axe in light and dark) | done (the section does not fold: decision item 12) |
| 21 | `generate_contract_baseline.py --check` current; `generate_protocol_schema.py --check` in sync (Evidence) | done for the engine side |

Fails before: on part C's head the two new files stop at collection (no `criteria_wording` module, no `method_choice`); the scripted-wizard and intent tests have no `not_reported` parameter.

Not verified: whether the wording checks find anything in a real review's criteria (record, "What cannot be verified"); the terminal wizard by hand in a real terminal (tested through the responder and the refusal function).

Evidence, part D engine side (`-n 4`):

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| targeted | `694c131a` (working tree) | `tests/inception`, `tests/cli`, the inception console tests, `tests/kits/protocol`, `tests/kits/agent`, `-m "not slow"` | 1076 passed | 84 s |
| full | `438d6a72` | contract baseline, protocol schema, contract schemas, two-study fixture, both ruff commands, `select_test_gate.py --check`, `git diff --check`; `uv run pytest -q -n 4 --junitxml` | current; in sync; exit 0; exit 0; clean; clean; OK; clean; 6260 tests: 6230 passed, 15 skipped, 15 failed: 14 tests whose drafts reach preview or genesis without a chosen rule (now refused, as answer 8 requires) or compare a new draft exactly, and the known `test_draft_store_lock` comparison; their drafts now choose the rule and the two lock tests compare the draft apart from the method fields | 936 s |
| targeted | next commit | the five failing files | 119 passed | 52 s |

The PR gate for part D runs once its screen is built.

The screen (spec 11 FINAL 2026-11-21, questions 3, 7 and 8 answered as recommended; decision items 11 to 20 PROPOSED):
- `components/inception-criteria.tsx`: step 5's criteria section ("Criteria", its written line), the two lists unchanged, the out-of-scope question moved here from Shape, the limits line, and "How you will screen" (`MethodQuestions`): the visibility question pre-selected, the not-reported rule with no option selected, options and order from the engine's `method_options`, the help with the measured figures, "Not chosen yet" and the earlier-draft sentence from the engine's `method`, "From the imported protocol". Continue is held, naming why, while the rule is unchosen; a save writes both values as shown.
- `components/inception-review.tsx`: the read-only group "How you will screen" (the two choices in words, "Not chosen yet", "Change" to the rule).
- `components/inception-shape.tsx`: the out-of-scope question is gone; one line says where it is asked; the stored items are kept.
- `lib/checks-copy.ts`: the five wording checks, `CRITERIA_WORDING_NOT_CHECKED` and `METHOD_RULE_UNCHOSEN` (with its earlier-draft sentence), en, fr and ar; the catalogue lists 59 ids. `components/assist-anchor.tsx`: a check's link reaches the rule's first option or the out-of-scope field.
- `lib/inception-api.ts`, `lib/inception-copy.ts`, `lib/assist-labels.ts`: the method types, the new keys (en, fr, ar), `field.out_of_scope`.
- `docs/ux/shared/final/03-guidance.md`: rows I-SH10 (repointed), I-C24 to I-C30, I-R22; counts 116, 34, 11, 161.
- Tests: `tests/inception-criteria-block.test.tsx` (12), the fake engine's `method` answer (`tests/fixtures/inception-engine.ts`, opt-in), `tests-browser/inception-criteria-block.spec.ts` (7 per project); existing tests follow the moved question (Shape, the criteria row read by its verbatim line).
- A part C test made robust: the agent check's focus assertion waits for the effect (it failed once under the full-suite load, passed alone three times); the same one-line change would suit part C's branch.

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| targeted | `c68486a8` (working tree) | `vitest run` of the step 5, Shape, Review, answers, checks and guidance files; `tsc` | 150 passed, then 12 of the new file; clean | |
| checkpoint | `c68486a8` | full `vitest run` | 1183 passed, 1 failed: part C's focus assertion under load (made to wait, `54a49ae0`) | 156 s |
| targeted | `e9f2b412` | `playwright test tests-browser/inception-criteria-block.spec.ts` (port 3127) | 14 passed after the group lost `aria-required` (axe) and the URL wait was corrected | 60 s |
| pr | `e9f2b412` | both ruff commands; contract baseline, protocol schema, contract schemas, two-study fixture; `git diff --check origin/main...HEAD` | exit 0; current; in sync; exit 0; exit 0; clean | |
| pr | `e8a0e1e3` | `uv run pytest -q -n 4 --junitxml` (full suite) | 6336 tests: 6321 passed, 15 skipped, 0 failed, 0 errors | 599 s |
| pr | `e8a0e1e3` | `npm run typecheck`; `vitest run` (full); `npm run test:browser` (build, then the full browser suite, port 3127) | clean; 83 files, 1184 passed; 684 passed, 12 skipped, 4 failed: two existing tests (end-to-end creation, Shape hints by keyboard, each in both projects) still used Shape's out-of-scope field | 127 s; 1206 s |
| targeted | next commit | the two tests moved to step 5's question (`tests-browser/inception.spec.ts`, `guidance.spec.ts`) | 6 passed (both projects) | 55 s |

The browser run rewrote the same four unrelated screenshots as in part C; they were restored, not committed.

Review round 1 of part D (`milestone-reviewer`, on `22f2ea6a`): **CHANGES** (lane RELEASE confirmed), 1 P2, 3 P3, 6 P4; no P1. The reviewer confirmed answer 8 on every path (new draft, earlier draft, import without a block, the terminal wizard, a scripted run refused before writing), that a chosen rule cannot be unset on either save path, genesis refused naming `METHOD_RULE_UNCHOSEN` with nothing written, DoD 18b (the intent's method copied; fingerprints kept), the wording checks never blocking with their honesty fixture, decision items 1 to 20 all PROPOSED and none breaking a DoD, and the guidance counts.

| # | Finding | Repair | Test (fails before: 1, 2, 3, 4 and 5) |
| :-- | :-- | :-- | :-- |
| P2-1 | Out-of-scope text typed without "Add" was dropped by Continue and "Save draft and exit" | the page's save applies the field as typed (semicolons and line breaks separate) | `review D round 1` > `finding 1` in `inception-criteria-block.test.tsx` |
| P3-2 | `METHOD_RULE_UNCHOSEN` had no refusal card on Review | a card in en, fr and ar, worded as `CRITERIA_UNDECIDED`'s ("Choose a rule on Concepts and criteria"); the fake engine's preview and genesis refuse it | `finding 2` (the card is known in three languages; Review shows it) |
| P3-3 | `--not-reported` was not documented; the inception-agent skill told agents to run a scripted interview that is now refused, and did not say the rule is the researcher's | the user guide (`init`, `inception`) and both skill copies name the flag, its values and its absence of default, and tell the agent to ask the researcher | `tests/inception/test_method_questions.py::test_the_inception_agent_skill_names_the_rule_wherever_it_scripts_the_wizard` (2) |
| P3-4 | Criterion texts in the new check sentences were `dir="ltr"` | the panel reads `a`, `b`, `criterion`, `inclusion` and `exclusion` with `dir="auto"` | `checks panel, M11b part D` > `quotes criteria in their own direction (RTL)` |
| P4-5 | The "0.6" mirror case scored 1.0 | a pair with 3 of 5 words shared both ways (0.6) and one at 0.4 | `test_the_mirror_share_is_the_constant` |
| P4-6, 7 | Decision item 19's `{side}` wording; the entry's and the record's stale status lines | corrected | (documents) |
| P4-8 | "other than" was two separate negation words, so "other" alone was dropped | only the phrase is a negation; "other" is a content word | `test_other_than_is_a_negation_only_as_the_phrase` |
| P4-10 | "From the imported protocol" stayed after the choice changed | shown only while the imported choice is the one chosen | (`finding 10`, a guard) |

Not taken: P4-9 (Review falls back to "after you decide" when a draft has no visibility value; the engine stores one for every new draft and the screen saves it, so the fallback only fills a draft from before part D); P4-10's first half (the method section under `DRAFT_INCOMPLETE`, a follow-up). Follow-ups for the researcher, outside part D's DoD: placeholder workspaces (`init --scaffold-only`, the Workspaces "Create") still sign `not_reported: "unclear"` without asking; an import of a protocol signed since 2026-11-08 carries the "unclear" genesis wrote without asking as chosen, and ignores later method amendments; the English test reads a French criterion holding "a" as English; the mirror rule's "or the reverse" flags a one-word exclusion whose word an inclusion holds (warnings only).

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| targeted | `47bf18e2` (working tree) | `tests/inception/test_criteria_wording_checks.py`, `test_method_questions.py` (`-n 4`); `vitest` of the step 5, checks and Review files; contract baseline | 33 + 2 passed; 55 passed; current | |
| pr (round 1 repairs) | `47bf18e2` | `uv run pytest -q -n 4 --junitxml` (full suite) | 6339 tests: 6324 passed, 15 skipped, 0 failed, 0 errors | 935 s |
| pr (round 1 repairs) | `47bf18e2` | `npm run typecheck`; `vitest run` (full); `npm run test:browser` (build, then the full browser suite, port 3127) | clean; 1187 of 1188 passed: `inception-criteria.test.tsx` failed once while the machine was loaded (the run took 271 s against 127 s before) and passed twice alone; 688 passed, 12 skipped, 0 failed | 271 s; 917 s |

Review round 2 of part D (on `198bdfe8`): **APPROVE** (lane RELEASE confirmed; the contract baseline current at head; 35 Python and 38 vitest targeted tests passed). Three P4 notes, recorded as follow-ups: the import-label test cannot fail (its draft has no import origin; a real test seeds an imported draft and changes the rule); after the researcher saves another rule the label compares against the stored draft and comes back (keeping the imported value in the origin's `carried` entry would fix it); the one full-run vitest failure was `inception.criteria > shows each criterion verbatim with its source; the generated one waits for you` (a test of 05's rows, passed twice alone).

**Part D: READY FOR PR** (not pushed). Branch `dev/m11b/part-d-step5`, stacked on part C (reviewed head `daaeaa92`) with `origin/main` `55755bd7`. Lane RELEASE: the CI matrix on the PR is the closure evidence, recorded after the push. Decision items 1 to 20 of part D wait for the researcher. Part C's final head is to be merged in when the main session sends it.

The researcher's answers to part D (main session, 2026-11-22): nineteen items accepted (11 "Accept"; 8 "Accept, with the weak spot", the French case a follow-up; 17 "Follow-ups"; the other fifteen "Accept as built"); **item 5 changed: "Shown, but I must confirm it"**. The push of part D is approved in advance on condition that the item 5 change passes the full gate and the `milestone-reviewer` approves the delta; the main session pushes, after part C. The follow-up on placeholder workspaces that sign `unclear` without asking is to be fixed in a follow-up PR after part D merges (not here).

The item 5 change (decision items 21 to 24, PROPOSED), built test first:
- Engine: the draft field `method_not_reported_source` (`imported`, `confirmed`, `chosen`, or null); the importer marks the rule `imported`; `method_choice` answers `chosen: false` and the `source` for it, so `METHOD_RULE_UNCHOSEN` blocks step 5, Review and genesis, with its own sentence (`METHOD_RULE_UNCHOSEN.imported`) and `details.imported` on a refusal; `keep_method_choice` keeps the source when a save omits it, refuses marking a confirmed or picked rule imported again, and makes a changed value `chosen`. The visibility question is carried as it is. The terminal wizard never starts from an imported protocol, so it is unchanged.
- Screen: "From the imported protocol: confirm this rule or choose another." with "Keep this rule"; keeping saves `confirmed` (label kept), choosing another saves `chosen` (label dropped), both read from the engine's `source`; the criteria step is asked again when the source changes in the tab (a bug the first test run showed: Continue stayed held after "Keep this rule"). Review: "From the imported protocol; not confirmed yet." Copy in en, fr and ar; the audit's row I-C30 names the two new keys.

| Item | Test | Fails before |
| :-- | :-- | :-- |
| an import marks its rule imported, carries the visibility | `tests/inception/test_method_questions.py::test_an_import_marks_its_rule_imported_and_carries_the_visibility_as_it_is` | yes (no field: `DRAFT_INVALID` extra input) |
| shown but blocking at step 5, Review and genesis, nothing written | `test_an_imported_rule_is_shown_but_blocks_step_5_review_and_genesis_until_confirmed` | yes |
| confirming clears the blocker and records the confirmation | `test_confirming_the_imported_rule_clears_the_blocker_and_records_the_confirmation` | yes |
| choosing another clears it and drops the mark; a save that names nothing keeps it | `test_choosing_another_rule_clears_the_blocker_and_drops_the_import_mark` | yes |
| a confirmed rule cannot be marked imported again | `test_a_confirmed_rule_cannot_be_marked_imported_again` | yes |
| the screen: shown, labelled, held; "Keep this rule"; another choice drops the label; Review's line | `apps/research-ui/tests/inception-criteria-block.test.tsx` "item 5" (3; they replace the guard that could not fail) | yes (Continue stayed held after "Keep this rule" until the step was asked again on the source) |

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| targeted | `d012e9c6` (working tree) | `tests/inception`, `tests/console/test_inception_api.py`, `tests/kits/protocol`, `tests/mcp`, `-m "not slow"`, `-n 4`; `vitest` of the step 5, checks, guidance audit and Review files; contract baseline, protocol schema | 664 passed; 80 passed, then 17 of the step 5 file (two waits lengthened: the screen draws in more than a second on a loaded machine); current; in sync | |
