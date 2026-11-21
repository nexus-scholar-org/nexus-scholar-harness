# M11b Criteria pilot

Branch: `dev/m11b/criteria-pilot-spec` (from `origin/main` at `1f218054`) · Lane: declared per part (proposed below: A, B and D **RELEASE**, C **STANDARD**) · Status: **SPECIFICATION, DRAFT for the researcher (2026-11-21); nothing decided, nothing built** · Fourth in the agreed order (plan §6, "After the acceptance run"); its build waits for M11a part C (see "What it assumes from M11a")

Short page for the researcher: [`M11b-criteria-pilot-for-review.md`](M11b-criteria-pilot-for-review.md). Screens (both `Status: DRAFT`): [`docs/ux/phase2-screening/final/13-criteria-pilot.md`](../../ux/phase2-screening/final/13-criteria-pilot.md) (draw the pilot, its result, revise a criterion) and [`docs/ux/phase0-inception/final/11-criteria-block.md`](../../ux/phase0-inception/final/11-criteria-block.md) (the change to Inception's step 5). Choices: `docs/decisions.md`, "2026-11-21 — M11b criteria pilot: the specification's choices" (PROPOSED).

Sources: `docs/roadmap/what-a-researcher-does.md` (step 3: "The criteria change after a pilot: 50 to 100 records are screened, the criteria turn out ambiguous, they are rewritten, and only then fixed"); `docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md` (findings 1, 2, 31, 36 and the section "Screening and agent drafts"); plan §6, row 4; `docs/decisions.md` entries "2026-11-20 — H-screening-drafts" (item 2: the method amendment beside the signed protocol; item 9: Inception does not ask) and "2026-11-19 — M10c" (items 9(a), 16, 21: what a moved fingerprint does); the Inception redesign decisions D1 to D15 (local branch `dev/ux/inception-redesign`, `04-recommendation.md`); `docs/architecture/DEVELOPER_COMPASS.md` §3; and the code at `1f218054`, checked by two `phase-auditor` runs (see "What exists, checked against the code").

## Goal

Let the researcher screen a small random sample of the accepted corpus under their criteria before the full screening, and show them where the criteria worked and where they did not. Let them revise a criterion with a recorded reason, as an amendment beside the signed protocol, so the decisions already made stay bound and the records a revision could change are shown again. Warn about criteria that mirror or contradict each other before any record is read, and ask the two method settings where the criteria are accepted rather than after screening has started.

## What a researcher does at this stage, and what the app offers today

**What a researcher does.** The protocol's criteria are written before any record is read, and they are wrong in ways that only reading shows: a criterion nobody can judge from an abstract, two criteria that say the same thing, a wording the second reader (a supervisor, or now an agent) reads differently. So 50 to 100 records are screened as a pilot, the criteria are rewritten, and only then fixed. The pilot and the revision are reported ("criteria were piloted on 50 records and refined"), and PRISMA-ScR expects deviations from the protocol to be stated.

**What happened on 2026-11-20.** The review had four inclusion and five exclusion criteria and 1,062 records. The wizard turned the proof answer into a criterion that is not a screening rule (finding 1) and lumped the out-of-scope answer into one exclusion (finding 2); five exclusions were typed by hand, several mirroring an inclusion ("RGB only" against "multispectral from a UAV"), and "uses a learned model" sat beside "or a dataset paper", so a dataset paper could not satisfy both. Nothing warned about either (finding 36). Blinding and the not-reported rule were fixed at genesis without a question; the researcher found out on Prepare that "Show beside the record" did nothing (finding 31). Agent drafts came back 83 to 85% Unclear; the rule was the main cause and the mirrored criteria doubled the chances of a `not_reported` answer. The fix for the rule (H-screening-drafts) is an amendment of the method beside the signed protocol. No such path exists for the criteria: changing one means a new workspace.

### What exists, checked against the code

Two `phase-auditor` runs at `1f218054` (read only, no network). Every line below was read in the code; "inferred" marks the two that were not run.

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

**Recommendation: A1, with the criteria version stamped by the engine.** **What happens to the pilot's decisions afterwards:** they are ordinary decisions, kept and counted, except those a revision could change, which are **shown again**: every Include, every Unclear (MAYBE), and every Exclude whose reason cites a criterion the revision touched. An Exclude for a criterion left untouched still holds, because one failed criterion is enough. A record shown again keeps its earlier decision in the log; the new decision supersedes it (`supersedes`, E8). Until it is decided again, its batch counts as not fully decided, so it cannot be approved (fail closed: compass §3). "Kept as pilot decisions, apart" was rejected: they are real decisions on real records, and putting them aside would make the researcher read 50 records twice. "Carried over unchanged" was rejected: an Include made under the old wording is not an Include under the new one.

**When a revision is allowed.** From the moment batches are prepared until the first batch is approved. The same rule (shown again) applies to every decided record, pilot or not, and the confirmation states how many records it will show again. After a batch is approved, a revision is refused (`CRITERIA_AMENDMENT_AFTER_APPROVAL`); changing criteria after publication stays a new screening (start from this protocol), as today. Before batches exist there is nothing to protect: a criterion is changed by going back to Inception.

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
- *Alternative:* a new id on every change of wording, rewording included. Simpler to state, but a clarification after a pilot is the common case, and the PRISMA counts would then split one criterion across two labels. Not recommended.

### (c) Contract decision or not

Under A1 nothing in Contract v1 changes (E16):
- `protocol.json` is not written after genesis, so the protocol schema and the fingerprint algorithm do not change.
- The reason code is a harness field of the event log; the locked `ScreeningDecision` keeps a free-text `reason`. The criteria version is a new engine-stamped field of the harness event log and of `proposals.jsonl`, not of a Contract v1 schema.
- The corpus snapshot and the batch files are not rewritten. The batch file still embeds the signed wording (E10); it stays as it is because it is hashed into every binding, and every reader takes the wording in force from the engine instead.
- `audit/criteria_amendments.jsonl` and the pilot file are side files outside the baseline, like `audit/method_amendments.jsonl`.

`generate_contract_baseline.py --check` must still answer "current" before and after each part.

**It is RELEASE in any case**: A1 adds public routes, refusal codes, persisted records, an engine-stamped field on decision events and drafts, and changes what decision intake accepts (`test_gate_policy.md`: public API semantics, artifact persistence). **It would also need a contract decision and a baseline regeneration** if the researcher chooses A2 or A3; if the criteria version, or the amended wording, had to appear in the published Contract v1 screening-decisions artifact (as a field, not as free text in `reason`); if the amendments file had to become a registered parent under the envelope's `inputs`; or if the PRISMA by-reason figure became a contract artifact. None is recommended.

## Scope recommendations

### (d) The pilot sample

- **Size 50** by default; the researcher can choose 20 to 100 (step 10). The note "50 to 100 records" is the usual practice; 50 keeps a solo reviewer's pilot to about half an hour at 30 seconds a record.
- **Drawn how:** simple random from the accepted snapshot's studies, with a seed the engine draws and records (`random.Random(seed).sample`, the snapshot id and the order of its studies as input, so the same seed on the same snapshot gives the same list). Records already decided are not drawn. Not stratified: a stratified draw needs strata the app does not have; records without an abstract are drawn like the others and labelled, because the full screening meets them too.
- **Stored:** `literature/screening/pilot/pilot_NNN.json` (`pilot_id`, `seed`, `n`, the snapshot id, the protocol fingerprint, the criteria version, `drawn_at`, `drawn_by`, and the list of `{study_id, batch_id}`), journal row `SCREENING_PILOT_DRAWN`. Inside `literature/screening/`, so a chase round archives it with the rest (E17).
- **Back to the main queue?** The pilot records stay in their batches; their decisions are ordinary decision events in those batches. When the pilot ends they are decided, so the main queue skips them, except those a revision shows again. There is no separate pilot store and nothing to merge.
- **A second pilot** after a revision is allowed: 50 more records not yet decided, a new seed, `pilot_002`. The result screen compares the two.
- **During the pilot the checklist opens by default** (E9: today it is closed by default and optional). It stays optional; the screen says "In the pilot your answers per criterion show which criteria are hard to judge." This is what lets the result say where the researcher chose Unclear and why.

### (e) What the researcher sees after the pilot

One screen, read from the engine (`GET /screening/pilot/{pilot_id}/result`), counts only, each with its denominator:

1. **The decisions:** n decided of N drawn; Include, Exclude, Unclear.
2. **Per criterion,** in protocol order, a row: how many exclusions it decided (as `EXC-nn` or `FAILS-INC-nn`); how often the researcher's checklist answered it "not reported" (of the records where the checklist was used); when agent drafts exist for the pilot records, how often the draft answered it `not_reported`, and how often the draft and the researcher disagreed on it (of the records where both answered).
3. **What this suggests,** a short list of observations, each from a fixed rule ((f), the pilot rules), each naming the criterion and the counts behind it, never an instruction: "EXC-05 decided no record in this pilot of 50. It may be rare, or covered by another criterion." Each has one action "Revise {id}" per criterion it names (two for a pair) and nothing else.
4. **Records,** filterable by criterion, by outcome, by "the agent disagreed": the titles, opening Triage on the record.
5. **The action bar:** "Revise a criterion" (opens the revise dialog), "Pilot 50 more records", "Screen the rest". "Screen the rest" records nothing; it goes to the queue.

**After a revision** the result keeps each pilot's numbers with the criteria version its decisions were made under, and counts a record shown again under the new version once it is decided again; it is recomputed when read, never stored. **There is no undo:** a revision is reversed by another revision (a reword back, an add), and both stay in the record.

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

| Observation | Rule (constants; n is the number of records where both answers exist) |
| :-- | :-- |
| Mirrored pair | Agent drafts: an exclusion answered `yes` exactly when an inclusion is answered `no`, in at least 90% of n ≥ 10 records |
| Exclusions that fire together | Agent drafts or checklist: two exclusions both `yes` in at least 90% of the records where either is `yes` (at least 5) |
| Hard to judge from the abstract | A criterion answered `not_reported` in at least half of the drafts, or of the checklist answers (n ≥ 10) |
| Never used | A criterion that decided no exclusion and was never answered against (exclusion never `yes`, inclusion never `no`) |
| Does most of the work | One criterion decided at least 60% of the exclusions (informative; says "check it is worded as you mean") |
| Many Unclear | At least 30% of the pilot decided Unclear |
| Read differently | The draft and the researcher disagree on a criterion in at least 25% of n ≥ 10 records |

The pilot rules catch the run's mirror without a model, from answers the agent already gives per criterion (E11). **Recommendation: rules only in M11b.** A meaning check would need a model call at Inception, its spend approved, its errors measured; the M10c critic over MCP can already be asked by the researcher's own AI client (not yet tried with a real client), and an in-app critic belongs with M10e. There is no strong reason to bring a model into this milestone.

### (g) Inception asks the two method settings

On step 5, in the criteria block after the two lists, a short section "How you will screen", two questions, each with a default selected and words that say what it costs. Stored in the draft (`method_blinding`, `method_not_reported`, new), written by genesis into the protocol's `method` block (today genesis writes the defaults, E2). Both can still be amended later from Prepare (E7).

1. **"When should the agent's draft for a record be shown to you?"**
   - "After you decide the record" (`reveal_after_decision`) · default, as today. Help: "You read each record without the agent's view first, and the app can measure how often the agent agrees with you."
   - "Beside the record, while you decide" (`show`). Help: "Faster to screen. The app can then not measure the agent against your own reading, because you saw its draft first."
2. **"When the title and abstract do not report a criterion, the agent's draft should…"**
   - "Exclude only on a clear failure; otherwise mark it Unclear" (`decisive_first`) · **recommended default for new reviews.** Help: "A record that clearly fails one criterion is excluded even if another is not reported."
   - "Mark it Unclear whenever a criterion is not reported" (`unclear`). Help: "The most cautious. In the 2026-11-20 review, 85% of drafts were Unclear under this rule."
   - "Exclude when an inclusion criterion is not reported" (`exclude`). Help: "The strictest. A record is excluded when its abstract is silent on something it must show." (The model's definition: an inclusion criterion not reported gives Exclude, `FAILS-INC-n`; `scholar_protocol/models.py:342-347`.)

**Who owns the default.** The engine, not the screen: a draft created after part D is created with `method_blinding: reveal_after_decision` and `method_not_reported: decisive_first` stored, so the screen shows what genesis will write. A draft created before part D has neither field; the screen shows the values genesis would write for it (the model defaults, `unclear`) with the note "This draft was started before this question existed; choose to change it", and genesis writes what is stored or, when nothing is, the model defaults. An imported protocol (`09-start-from-protocol`) that carries a `method` block fills the two questions from it.

The cost of the recommended default: on the frozen 1,644-record set (Haiku 5.5), the lower bound of the agent's include recall was 92.2% under `decisive_first` and 96.8% under `unclear`; the excludes the agent caught went from 1.9% to 78.6%. Existing protocols do not change; the model's default stays `unclear`; only the Inception screen pre-selects `decisive_first`.

### (h) How a revision is recorded and reported

**The amendment row** (`audit/criteria_amendments.jsonl`, one line per revision): `amendment_id` ("CRA-" + 24 hex), `op` (`reword`, `split`, `merge`, `remove`, `add`, `reason_category`), `side`, `from` (list of `{id, text, reason_category}`), `to` (same), `reason` (one sentence, required, at most 500 characters), `criteria_version_before`, `criteria_version_after`, `protocol_fingerprint`, `pilot_id` (the pilot in progress, or null), `decided_at_time` (how many decided records existed), `shown_again` (how many, by outcome), `amended_by`, `amended_at`.

**Journal rows:** `SCREENING_PILOT_DRAWN` (pilot id, n, seed), `PROTOCOL_CRITERIA_AMENDED` (amendment id, op, from and to ids, the reason, the versions, the counts), and on publish the sha256 of `audit/criteria_amendments.jsonl` in the publish row. `SCREENING_CRITERIA.md` is rewritten as the criteria in force with a section "Amendments" listing each one; the earlier file is backed up to `audit/amended/<UTC stamp>/` as M10c 9(a) does.

**The methods paragraph** (`screening/export.py` `build_methods`, E14) gains, after the method sentences:
- with a pilot: "The screening criteria were piloted on {n} records drawn at random from the {N} records of the corpus (seed {seed}){, and on {n2} more after the first revision}."
- per amendment: "On {date}, {criterion} was {reworded | split into … | merged with … | removed | added}: '{from}' became '{to}'. Reason: {reason}. {k} records already decided were screened again." When it came after the pilot: "… after {d} records had been decided …".
- with no amendment: "The criteria were not changed after the protocol was signed."

The PRISMA figure is unchanged in shape; its "excluded, by reason" counts name the criteria in force (b).

### (i) What "check the agent on your labels" reuses from the pilot

The pilot's decisions are the labels. "Check the agent on these 50 records" on the result screen calls the existing calibration route (E13) with the pilot's decided `study_ids`, and always sends a model: the setup's `last_model` (`GET /proposals/setup`), else the run screen's constant `claude-haiku-5-5` (H-screening-drafts item 6). The route's body defaults to Opus 5.5, and the screen must never rely on that default (the $7.59 of finding 32). The dialog names the model, the count and the estimate, which comes from the existing `POST /proposals/runs {estimate_only: true, scope: {study_ids}}` (`console/api/screening_v1.py:987-1042`); about $0.01 for 50 records on Haiku 5.5 (scaled from the run's $0.22 for 1,062). The result fills the agent columns of (e) and the per-criterion disagreement. `splits_by_criterion` (E12) gains its denominator. `prompt-gate measure --scope all` stays the command-line route and is unchanged. Drafts made under an earlier criteria version are labelled "made under the earlier wording" and are not counted in agreement, calibration or the queue's order; the run screen offers "Draft again the {n} records whose draft predates the revision", with its estimate. No spend happens without that dialog.

## Definition of done

Each item is checked by a test named in the build record, unless it says "live".

**Criteria amendments (part A)**
- [ ] DoD 1. `POST /api/v1/screening/criteria/amendments {op, side, ids, text?, reason_category?, reason, confirm}` (desktop only) records a revision: one line of `audit/criteria_amendments.jsonl`, one `PROTOCOL_CRITERIA_AMENDED` row; `protocol.json`, the snapshot and the batch files keep their bytes.
- [ ] DoD 2. The criteria in force are the signed list plus the amendments under the current fingerprint, oldest first, with a version number; one function reads them, and every reader uses it: the agent run, the draft reader, the reason check at intake, Triage's criteria and checklist, the batch instructions shown to an agent, the agreement read, the export. A test lists the readers of `screening_criteria` and fails on a new one that bypasses the function.
- [ ] DoD 3. Ids follow (b): reword keeps the id; split, merge and remove retire; a new id takes the next number on its side, never a used one; `REASON_CODE_RETIRED` on a new decision citing a retired id; earlier events stay valid.
- [ ] DoD 4. Every new decision event and every new draft carries the engine-stamped `criteria_version`; an event without it is version 1. A browser cannot send it.
- [ ] DoD 5. After an amendment, the records shown again are exactly: Include, MAYBE, and Exclude citing a touched criterion, for decisions made under an earlier version; the queue lists them (`view=recheck`); a batch holding one is not fully decided for approval.
- [ ] DoD 6. A revision is refused before batches exist (`CRITERIA_AMENDMENT_NO_BATCHES`), after a batch is approved (`CRITERIA_AMENDMENT_AFTER_APPROVAL`), without a reason or `confirm`, for an unknown or retired id, or one that changes nothing (`CRITERIA_AMENDMENT_INVALID`). A dry call (`confirm: false`) answers what it would change: the new ids and how many records it would show again, by outcome.
- [ ] DoD 7. A revision that leaves a side with no criterion in force is refused (`CRITERIA_SIDE_EMPTY`), as genesis refuses a missing side.
- [ ] DoD 7b. `GET /api/v1/screening/criteria` answers the criteria in force (id, side, text, reason category, the version each wording dates from), the retired ids, the current version and the amendments; the revise dialog and Triage read it.
- [ ] DoD 8. `SCREENING_CRITERIA.md` is rewritten with the criteria in force and an "Amendments" section; the earlier file is backed up under `audit/amended/<stamp>/`.
- [ ] DoD 9. Drafts made under an earlier version are labelled and left out of agreement, calibration and queue order; the run setup counts them.
- [ ] DoD 10. The methods paragraph reports each amendment and, with no amendment, says the criteria were not changed; the publish journal row carries the sha256 of the amendments file.

**The pilot (part B)**
- [ ] DoD 11. `POST /api/v1/screening/pilot {n, confirm}` draws n (20 to 100, default 50) undecided records at random with a recorded seed; the same seed on the same snapshot gives the same list; the file and `SCREENING_PILOT_DRAWN` are written. Refused before batches exist, after a batch is approved, while a pilot has undecided records (`PILOT_OPEN`), or when fewer undecided records remain than asked. A dry call (`confirm: false`) answers n, the undecided count and the expected time, and writes nothing.
- [ ] DoD 11b. `GET /summary` gains a `pilot` block (the open or last pilot's id, n, decided, and how many records wait to be shown again), so every screen knows a pilot is open without a new route.
- [ ] DoD 12. `GET /queue?view=pilot` lists the pilot's records in the drawn order; during a pilot the checklist opens by default (a setting the queue answers, not a browser guess).
- [ ] DoD 13. `GET /screening/pilot/{id}/result` answers (e): counts per outcome; per criterion the exclusions it decided, the checklist's `not_reported`, and with drafts the draft's `not_reported` and the disagreements, each with its denominator; the observations of (f) with their counts; for a second pilot, the first one beside it.
- [ ] DoD 14. "Check the agent on these records" sends the pilot's decided ids to `POST /proposals/calibrations` with an explicit model, always (a UI test fails when the body has no `model`); the estimate comes from `POST /proposals/runs` with `estimate_only` and the same ids. The route's own Opus default is not changed here (a public default; changing it is a separate decision).
- [ ] DoD 15. `splits_by_criterion` gains `answered_by_both` per criterion; old clients still read the count.

**Screens (part C)**
- [ ] DoD 16. Prepare offers "Pilot your criteria first" beside "Screen everything", per the screen spec; Triage shows the pilot's banner and progress; the result and revise screen and its dialog follow `13-criteria-pilot.md`; every state has its words in en, fr and ar; axe passes in light and dark.
- [ ] DoD 17. The revise dialog shows, before anything is recorded, the new ids and the records it will show again by outcome, and needs the reason.

**Inception (part D)**
- [ ] DoD 18. Step 5's criteria block asks the two method settings with the defaults and words of (g); a new draft is created with the defaults stored, so the screen and genesis agree; genesis writes them into `method`; the preview lists them; a draft from before part D shows and compiles the model defaults (`unclear`) until the researcher chooses.
- [ ] DoD 19. The five wording checks of (f) in the catalogue, at the field and at Review, never blockers, dismissible with a reason (M10b rule).
- [ ] DoD 20. The criteria are laid out as direction A's criteria block (D13) inside today's step 5, as M11a did for the concepts block; the out-of-scope question is asked in this block (D6).

**Closure**
- [ ] DoD 21. `generate_contract_baseline.py --check` current before and after each part; `generate_protocol_schema.py --check` unchanged.
- [ ] DoD 22 (live). The researcher pilots the criteria of a real review (50 records), revises at least one criterion, and reports in this record what the pilot showed and whether the observations were right.

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

## Parts, one PR each

| Part | Contents | Lane | Why that lane | Depends on |
| :-- | :-- | :-- | :-- | :-- |
| **A. Criteria in force** | `screening/criteria.py` (criteria in force, versions, retired ids, shown-again set), the amendment route and file, refusal codes `CRITERIA_AMENDMENT_INVALID`, `CRITERIA_AMENDMENT_NO_BATCHES`, `CRITERIA_AMENDMENT_AFTER_APPROVAL`, `CRITERIA_SIDE_EMPTY`, `REASON_CODE_RETIRED`; every reader moved to it; `criteria_version` on events and drafts; `view=recheck` and the approval gate; `SCREENING_CRITERIA.md`; the methods sentences | RELEASE | public route and refusals, persisted record, new engine field on events, decision intake changes | none |
| **B. The pilot** | `screening/pilot.py` (draw, file, result, observations), routes `POST /pilot`, `GET /pilot/{id}/result`, `view=pilot`, the checklist default during a pilot, refusal `PILOT_OPEN`, `SCREENING_PILOT_DRAWN`, the calibration call with an explicit model, `answered_by_both` | RELEASE | public routes, persisted record, an additive field on a public answer | A |
| **C. Screening screens** | Prepare's entry, Triage's pilot banner and recheck view, the result and revise screen (spec `13-criteria-pilot`), the run screen's "Draft again", en/fr/ar, axe | STANDARD (UI) | browser only, over A and B | A, B; M8b-triage-highlights if it is merged first (both touch Triage) |
| **D. Inception step 5** | the criteria block (D13), the out-of-scope question in it (D6), the method questions, draft fields and genesis, the five wording checks (spec `11-criteria-block`) | RELEASE | the inception draft API and the protocol genesis writes change; new check ids in a public preview | M11a part C merged |

Inner and checkpoint gates by `scripts/select_test_gate.py --changed main`; the full suite once per PR. No live call and no model call in any test: drafts and calibration through the existing doubles.

## Reused and new

| Need | Reused | New |
| :-- | :-- | :-- |
| An amendment beside the signed protocol | the method amendment pattern: file, journal row, fingerprint filter, values in force, methods sentence (E7) | `criteria_amendments.jsonl`, ops on criteria, versions, retired ids |
| Superseding a decision | `supersedes` on decision events (E8) | the shown-again set and `view=recheck` |
| Fail closed before approval | the "fully decided" rule of approval (09-publish) | a record shown again counts as undecided |
| Reason codes | `valid_reason` (E8), `FAILS-INC-nn` | reads the criteria in force; `REASON_CODE_RETIRED` |
| Draft outcome under the rule in force | `outcome_in_force` (E11) | criteria version on drafts; earlier-wording label |
| Per-criterion answers | agent draft answers (E11), the optional checklist (E9) | the pilot's rules |
| Agreement per criterion | `splits_by_criterion` (E12) | its denominator |
| Check the agent on your labels | `POST /proposals/calibrations` (E13) | called with the pilot's ids and an explicit model |
| Checks at Inception | the M10b catalogue and `_criteria_checks` (E15) | five wording checks |
| Method at genesis | `MethodConfig` and genesis's method block (E2) | two draft fields and two questions |
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
7. **The method default.** Pre-selecting `decisive_first` trades some of the agent's include recall (lower bound 96.8% to 92.2% on the measured set) for drafts that decide; on a different review the trade may differ.

## What cannot be verified without a real review

- Whether 50 records show anything the researcher did not already know, and whether the observation thresholds (90%, 50%, 60%, 30%, 25%) are useful or noisy.
- Whether the wording checks find anything in real criteria; the run's own mirror shares no word and is caught only by the pilot rules.
- How many records a real revision shows again, and how long the re-check takes.
- Whether drafts after a revision become less Unclear (needs a paid run).
- How the researcher wants a revision worded in a methods section; the sentences above are a proposal.
- DoD 22: the researcher's own pilot.

## Open questions

In [`M11b-criteria-pilot-for-review.md`](M11b-criteria-pilot-for-review.md), in order, contract questions first, with recommendations and costs; the PROPOSED entry in `docs/decisions.md` holds the same items. The two screen drafts carry their own screen-level questions, settled when each spec is made FINAL at the start of its part.
