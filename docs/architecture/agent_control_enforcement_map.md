# Agent-Control Enforcement Map (AG-00) — LLM-assisted screening

**Lane:** `FAST` (evidence-based assessment; one new docs file, no runtime change).
**Verdict carried:** `BLOCKED_BASELINE_DRIFT` for the working tree (see §2).
No contract readiness is certified. No remediation was performed.

## 0. Task context capsule

```yaml
task: AG-00-agent-control-enforcement-map
delivery_lane: FAST
owner_repo: nexus-scholar-org/nexus-scholar-harness
base_sha: 1c4255e
head_sha: 1c4255e
branch: main
allowed_paths:
  - docs/architecture/agent_control_enforcement_map.md
immutable_boundaries:
  - docs/architecture/contract_v1_baseline.json (do not regenerate)
  - src/scholar_harness/contracts/** (read-only for this task)
  - tools/** (read-only; toolkit-sync rule applies)
  - all pre-existing user modifications (preserved, not absorbed)
acceptance_ids: [AG-00-scope, AG-00-drift, AG-00-workflow, AG-00-map, AG-00-vocab, AG-00-packet]
open_findings: []
known_baseline_failures:
  - baseline --check fails on working tree (1 file; HEAD is clean; see §2)
evidence:
  - command: git status --short + git log -3 --oneline --decorate
    commit: 1c4255e
    result: recorded (8 modified tracked files, 1 untracked file)
  - command: uv run python scripts/generate_contract_baseline.py --check
    commit: 1c4255e
    result: FAIL (exit 1, drift message)
  - command: uv run python scripts/generate_contract_schemas.py --check
    commit: 1c4255e
    result: PASS (exit 0)
  - command: uv run python scripts/generate_two_study_contract_fixture.py --check
    commit: 1c4255e
    result: PASS (exit 0)
  - command: uv run python scripts/generate_nexus_scholar_pins.py --check
    commit: 1c4255e
    result: PASS (exit 0, pins in sync)
  - command: read-only hash comparison of 49 locked files (canonical LF normalization)
    commit: 1c4255e
    result: 48/49 match worktree; 49/49 match HEAD (see §2)
next_gate: none (assessment deliverable; no executable gate claimed)
stable_sources:
  - docs/architecture/DEVELOPER_COMPASS.md@1c4255e (§1-§5, §7)
  - docs/architecture/contract_v1_baseline.md@1c4255e (mandatory start check)
  - src/scholar_harness/contracts/models.py@1c4255e
  - src/scholar_harness/contracts/acceptance.py@1c4255e
  - src/scholar_harness/screening/batcher.py@1c4255e
  - src/scholar_harness/screening/collector.py@1c4255e
```

**Working-tree baseline (preserved, not modified):** `M .opencode/agent/reviewer.md`,
`M apps/research-ui/AGENTS.md`, `M apps/research-ui/README.md`,
`M apps/research-ui/docs/GATES.md`, `M apps/research-ui/tests/home-page.test.tsx`,
`M apps/research-ui/tests/i18n-render.test.tsx`,
`M apps/research-ui/tests/keyboard-traversal.test.tsx`,
`M docs/architecture/research_ui/AGENT_WORK_PACKETS.md`,
`?? docs/architecture/inception_recon_scientific_review.md`.
Only `.opencode/agent/reviewer.md` is in the locked baseline set; the rest are
outside the contract baseline scope and were not inspected for this assessment.

**Governing sources read once:** `AGENTS.md`, `DEVELOPER_COMPASS.md`,
`contract_v1_baseline.md`, `wp01_packet_c_reference.md`, `test_gate_policy.md`,
`agent_context_protocol.md`, both role skills
(`.agents/skills/doer-contract/SKILL.md`, `.agents/skills/critic-contract/SKILL.md`),
role prompts (`.opencode/agent/screener.md`, `screening-critic.md`, `adjudicator.md`,
`reviewer.md`), `contracts/models.py`, `contracts/acceptance.py`,
`screening/batcher.py`, `screening/collector.py`, `agent_screen.py`,
`screening/report.py` (header), `console/api/screening.py`, `console/api/audit.py`,
`workspace/audit.py`, `verification_identity.py`,
`tools/scholar-search-kit/src/scholar_search/screening.py`,
`tools/scholar-agent-kit/src/scholar_agent/calibration.py` (§1–§2),
`tests/test_screening_migration.py` (header, read only),
`tests/console/test_console_screening.py` (header, read only).
No test suite was executed; no test result is claimed. UI code was not inspected
(no workflow claim in this map depends on UI rendering).

**Source-of-truth conflicts:** none encountered. Per the Compass (§1, §4), the
Compass and canonical `main` govern implementation status (WP-01 packets adopted
through E4 with qualified closure), while `contract_v1_baseline.md` governs the
frozen contract semantics. This assessment uses both as the Compass directs.

## 1. Scope

Evidence-based assessment of which controls **already govern** an LLM-assisted
screening workflow, where each control is **actually enforced at runtime**, and
the **smallest missing boundary** keeping agent recommendations separate from
authorized scientific decisions. Facts (§2–§4), interpretations (assessment
statuses), and proposals (§6, and "smallest missing behavior" cells) are kept
separate. Absence conclusions are scoped to the inspected path.

## 2. Drift-check results and limitations

| Check | Result |
|---|---|
| `generate_contract_baseline.py --check` | **FAIL** (exit 1): `Contract baseline drifted: regenerate docs\architecture\contract_v1_baseline.json` |
| `generate_contract_schemas.py --check` | PASS (exit 0, no output) |
| `generate_two_study_contract_fixture.py --check` | PASS (exit 0, no output) |
| `generate_nexus_scholar_pins.py --check` | PASS (exit 0, pins in sync) |

**Precise difference (read-only, canonical LF hashing per
`scripts/generate_contract_baseline.py:58-61`):** the locked-file set is
identical (49/49 paths, no extras, no missing). Exactly one hash mismatches:

- `.opencode/agent/reviewer.md` — recorded `80077d4b…`, working tree `8c0f8126…`,
  `HEAD` (`git show HEAD:.opencode/agent/reviewer.md`) `80077d4b…` = recorded.

So the **inspected committed state (`1c4255e`) is baseline-clean**; the drift is
a **local working-tree modification**, confirmed by
`git diff HEAD -- .opencode/agent/reviewer.md`: frontmatter changed from
`edit: deny` / `bash: ask` to `edit: allow` / `bash: allow`, while the body
still claims *"You are read-only: file edits are denied…"*
(`.opencode/agent/reviewer.md:9-13`). This historical lead is therefore
confirmed as a **current working-tree fact**, not a committed-state diagnosis.

**Governing rule and disposition.** `contract_v1_baseline.md:60-72` ("every
implementation agent must run [the checks]; if baseline verification fails, stop
with `BLOCKED_BASELINE_DRIFT`; do not update the manifest") and Compass §5
require stopping **implementation / remediation** work. This task is explicitly
not implementation (no runtime, skill, contract, schema, fixture, pin, config,
or architecture change was made; nothing was regenerated). The assessment
therefore **proceeds as read-only evidence gathering while carrying
`BLOCKED_BASELINE_DRIFT` for the working tree**: it does not certify contract
readiness, does not proceed into remediation, and treats the reviewer.md
permission weakening as an agent-control finding (§4, row 12) rather than
repairing it. The assessment's factual basis is the committed state at
`1c4255e` plus the observed working-tree delta, distinguished above.

**Limitation:** a passing check establishes consistency with the recorded
baseline, not scientific correctness or complete runtime adoption.

## 3. Current screening workflow (as inspected)

| # | Transition | Producer | Consumer / validation | Write path | Publication boundary |
|---|---|---|---|---|---|
| 1 | Accepted screening batch | `cmd_prepare` (`screening/batcher.py:190-418`): verifies `protocol.json` fingerprint equals the accepted corpus generation (`:231-236`), builds `ScreeningBinding` + deterministic `run_id`/`batch_id`/`artifact_id` (`:271-315`), calls `accept_artifact` (`:340-352`) | `accept_artifact` (`contracts/acceptance.py:232-519`): schema → context → parent → binding/candidate checks; `SCREENING_BATCH_ID_MISMATCH` / `SCREENING_BINDING_MISMATCH` / `DECISION_OUTSIDE_BATCH` (`:446-476`) | Accepted envelope `artifacts/screening_batch/<id>.json` + `audit/artifact_registry.json` (atomic, `:552-621`); handoff `literature/screening/batch_NNN.json` + `MANIFEST.json` (`:366-404`) | Registry entry + `ARTIFACT_ACCEPTED` journal event (`:574-588`) |
| 2 | Assigned agent work | Handoff file's embedded `agent_instructions` (`batcher.py:68-138, :376-378`) + `MANIFEST.json` `PENDING` rows | None found in inspected path: the pipeline "stops… an agent reads each batch" (`AGENTS.md:30-31`); assignment is a file-handoff convention, not a recorded tasking | `batch_NNN.json` (mutable, unaudited) | No assignment ledger; `status` only reports file presence (`collector.py:49-91`) |
| 3 | Screening recommendation | Agent (any file writer) producing `batch_NNN_decisions.json` (raw array or `{"batch","decisions","reviewed_by","timestamp"}` wrapper; `batcher.py:147-183`), **or** console `POST /api/v1/screening/batch/{n}/decisions` (`console/api/screening.py:98-155`) | Console path: batch-index match, non-empty list, per-record validation, **membership** vs batch papers (`:109-130`); agent-file path: validated later at collection | `batch_NNN_decisions.json` (agent path: uncontrolled writer; console path: atomic temp+replace, `:92-95, :141`) | None at this stage: recommendation files are **not** accepted artifacts and are absent from `artifact_registry.json` |
| 4 | Technical validation | `cmd_collect` (`screening/collector.py:99-796`): wrapper provenance load (`:555-561`), parent-batch resolution from **registry** (never the handoff, `:211-244, :580-583`), membership validation (`:246-281` dual, `:588-611` single), checklist derivation when present (`:620-632`), `ContractDecision` mint (`:663-706` / dual `:322-446`), per-batch `accept_artifact` (`:752-770` / dual `:529-538`) | Same `accept_artifact` gate as row 1, plus `VerificationIdentityRefused` bridge-or-refuse before any publication (`:152-181`, codes in `verification_identity.py:29-36`) | Accepted `artifacts/screening_decisions/<id>.json` + registry; `.rejected` renames on membership/acceptance failure (`:607-609, :766-768`); `MANIFEST.json` statuses updated even on failure (`:779-785`) | `ARTIFACT_ACCEPTED` / `ARTIFACT_REJECTED` per batch; collection raises `RuntimeError` on any missing/invalid/rejected batch (`:787-796`) — "refusing unbound heuristic fallback" (`:549-551`) |
| 5 | Scientific review | `screening-critic` role (declared) | Declared axes + stratified independent re-screen (`.opencode/agent/screening-critic.md:16-26`); `critic-contract` gate: deterministic GREEN never overrides critic FAIL (`SKILL.md:19-23`) | Assigned critique artifact (declared only; path per task packet) | **No harness gate**: `cmd_collect` takes only `workspace_dir` and never requires a critique artifact |
| 6 | Authorization of final decision | None found in inspected path | `reviewed_by` / `screener_id` are free strings with honest fallbacks (`agent-unknown`, `agent-legacy`, `1970-01-01T00:00:00+00:00`; `batcher.py:165-183`, `collector.py:663-672`); `model_id`/`prompt_version` optional passthrough (`:355-356, :701-702`); no identity registry or authority check | `ContractDecision.screener_id` / `method` fields | Single-screener accepted decisions are a 1:1 harness transform of the recommendation — no separate authorization record exists |
| 7 | Decision collection | `cmd_collect` single path (`:541-775`) and dual path (`:199-538`) | Dual: both screener decisions required, provenance-complete (`:322-358`), disagreement requires adjudication with **exact** `parent_decision_ids == {s1, s2}` (`:380-396`); agreement mints `COMPOSED` consensus (`:398-420`). Single: no coverage or duplicate-entry check found (see §4 rows 16–17) | Accepted per-batch `screening_decisions` artifacts (dual preserves `[s1, s2, final]` per study, `:422-426`); legacy copy archived to `screening/legacy/` (`:773-775`) | Fail-closed: any missing/invalid/rejected batch aborts before partition outputs (`:787-796`) |
| 8 | Authoritative output + audit | Partition (`tools/scholar-search-kit/src/scholar_search/screening.py:429-496`) → `literature/included.json`, `excluded.json`, `conflicts.json`, `prisma_screening_report.md`, `prisma_report.json` (`collector.py:810-836`) | Borderline confidence `0.40–0.70` flagged to `conflicts` (`screening.py:476-477`); counts from `raw/provenance_manifest.json` when present (`collector.py:798-808`) | Plain JSON/Markdown files — **not** Contract-accepted artifacts, no registry entry | Audit: acceptance events (`ARTIFACT_ACCEPTED`/`ARTIFACT_REJECTED`, `contracts/acceptance.py:202-229, 574-588`), console `SCREEN_DECISIONS` (`console/api/screening.py:145-153`), all via append-only `workspace/audit.py:144-210` (server-minted `EVT-*`, uppercased action/status); collector's own refusal paths otherwise use logger + exceptions |

## 4. Enforcement map

**Status definitions.** `ENFORCED_IN_INSPECTED_PATH` — runtime code in the
inspected path rejects or gates the behavior (cite the check).
`PARTIALLY_ENFORCED` — part of the control is runtime-gated, part is not.
`DECLARED_ONLY` — stated in a skill, role prompt, schema, or architecture doc
with no runtime gate found in the inspected path. `NOT_FOUND_IN_INSPECTED_SCOPE`
— neither declaration nor gate found where inspected (not a whole-system claim).
`UNVERIFIED` — evidence exists but was only read, not executed, and execution is
needed. `NOT_APPLICABLE` — control does not apply to this workflow step.

Evidence-strength rule applied throughout: code cited by file:line was
**inspected**; tests named were **read, not executed**; the only **executed**
evidence in this assessment is the four drift checks (§2). Dated completion
records (Compass packet statuses) are cited as records, not as re-verification.

| Control | Existing source of truth | Runtime enforcement point | Evidence and limitations | Assessment status | Smallest missing behavior, if any | Verification needed |
|---|---|---|---|---|---|---|
| 1. Assignment to an exact batch and frozen protocol | `screening/batcher.py:231-236` (fingerprint equality), `:271-292` (binding), Compass §6 (minimum decision provenance) | `cmd_prepare` refuses on protocol/corpus mismatch (`sys.exit(1)`); batch acceptance binds `protocol_fingerprint`/`corpus_fingerprint`/`binding` | Inspected code. Limitation: assignment itself is a file-handoff convention (`AGENTS.md:30-31`); no tasking/assignee record; `status` reports file presence only (`collector.py:49-91`) | `PARTIALLY_ENFORCED` | Record the assignment (batch, assignee, protocol/corpus fingerprints) where the handoff is created; out of scope for the §6 packet except as a referenced input | Execute `tests/test_screening_migration.py` (read only for AG-00) against a protocol-mismatch fixture |
| 2. Immutable parent references and stale-input rejection | `contracts/acceptance.py:353-431` (parent resolution, hash, type), `:433-476` (screening binding/candidates); `_REQUIRED_PARENT_TYPE` (`:40-45`) | `accept_artifact` + collector membership checks against the **accepted parent artifact**, never the mutable handoff (`collector.py:216-221, :580-583`); stale/missing/cross-workspace parents rejected with typed codes | Inspected code. Strength: collector comments state the rationale explicitly. Limitation: handoff JSON remains mutable/unaudited by design | `ENFORCED_IN_INSPECTED_PATH` | None for screening parents; keep the "never trust the handoff" rule literal in any new gate | Existing `tests/test_contract_acceptance.py` (read, not executed) + one stale-batch collect test in the §6 packet |
| 3. Permitted source access; source text as untrusted data | Batcher embeds title/abstract/venue/doi from `verified.json` via alias lookup (`batcher.py:244-264, :354-364`); prompt embeds papers as JSON (`:101-106`) | No source-text execution found in the inspected screening path (papers are data in JSON); **no** sandbox, allow-list, or prompt-injection boundary found in the inspected path | Inspected code (negative result scoped to `screening/` + console screening API). Role prompts say "apply only the supplied criteria… do not use domain priors" (`screener.md:20-27`) — declared, not runtime-enforced | `PARTIALLY_ENFORCED` | Explicit untrusted-data handling note at the batch boundary (no new runtime in the §6 packet; packet must not accept new source-execution surface) | A prompt-injection probe test is future work, not part of the §6 packet |
| 4. Role boundaries; prevention of unauthorized writes | Doer invariant "write atomically and only to the assigned artifact path" (`doer-contract SKILL.md:6`); critic "only permitted write is the critique" (`critic-contract SKILL.md:8`); console writer constrained to `batch_NNN_decisions.json` with membership check (`console/api/screening.py:88-141`) | Console path: path-fixed, atomic, membership-gated. Agent-file path: **no writer authentication, no path lock** — any process can create/overwrite `batch_NNN_decisions.json` before `collect`; `prepare --force` guard (`batcher.py:204-213`) protects batches, not decisions | Inspected code. No permission-enforcement code found in `src/` for `.opencode/agent` frontmatter (grep for permission enforcement: no hits) — frontmatter is a host-convention declaration, not a harness gate | `PARTIALLY_ENFORCED` | §6 packet must not rely on frontmatter; it should gate at collection (coverage + authorization record), which is host-independent | Attempt an out-of-batch write via console API (expect 422) — existing `tests/console/test_console_screening.py` covers this shape (read, not executed) |
| 5. Separation of agent recommendations from final screening decisions | Distinct artifacts exist: raw `batch_NNN_decisions.json` (recommendation, unregistered) vs accepted `artifacts/screening_decisions/*.json` (harness-minted `decision_id`, `method`, `screener_id`; `collector.py:678-706`) | Harness minting + acceptance is real, but single-screener acceptance is a 1:1 transform of the recommendation with **no independent authorization step**; legacy `included.json`/`excluded.json` conflate further (plain files, no acceptance) | Inspected code. This is the assessment's central gap: the transform is technical, not authorizing | `PARTIALLY_ENFORCED` | **The §6 packet** (authorization-before-publication record; see §6) | Deterministic test: collect without authorization record must preserve the accepted recommendation artifact while refusing `included.json`/`excluded.json` |
| 6. Harness-controlled review requirements | `screening-critic.md` (stratified re-screen; GREEN cannot override FAIL) | **None found**: `cmd_collect(workspace_dir)` signature admits no critique input and checks for none | Inspected code (negative result, full `collector.py` read). Declared gate is strong on paper; runtime gate is absent | `DECLARED_ONLY` | Do not add a mandatory-critique gate in the §6 packet (that would expand scope); the authorization record in §6 is compatible with a later review-requirement packet | N/A for §6; a future packet would need a critique-presence check + FAIL-blocks-collection test |
| 7. Reviewer identity and authority to approve | None (no reviewer-identity model in the inspected screening path) | **None found**: `reviewed_by` defaults to `"console"` (`console/api/screening.py:84`) or free agent strings with `agent-unknown`/`agent-legacy` fallbacks (`batcher.py:165-183`); `screener_id` falls back to `reviewed_by` (`collector.py:671-673`) | Inspected code. Honest labeling of unknown provenance is a strength, but it is not identity or authority | `NOT_FOUND_IN_INSPECTED_SCOPE` | §6 packet defines the authorization record's identity field (which existing workspace actor vocabulary it reuses) — flagged as a required architecture decision (§6), not assumed | N/A (decision needed before tests can assert authority) |
| 8. Preservation of original recommendations and human overrides | Dual path preserves `[s1, s2, final]` with lineage (`collector.py:422-426`); single path archives a legacy copy (`:773-775`); failures rename to `.rejected` instead of deleting (`:607-609, :766-768`) | Partially runtime: archive + rename are real. Gap: console overwrite is atomic replace with **no version chain** (`console/api/screening.py:92-95`); a human override is file-shape-identical to an agent recommendation (only `reviewed_by` differs, free string) | Inspected code | `PARTIALLY_ENFORCED` | §6 packet: authorization record must reference the exact recommendation hashes it authorizes, so overrides are distinguishable by lineage | Test: authorize → overwrite recommendation → old authorization no longer validates the new file |
| 9. Scientific uncertainty and unresolved cases | Model layer preserves them: `ScreeningDecisionValue` includes `MAYBE`/`CONFLICT` (`models.py:90-94`); screener role forbids collapsing uncertainty (`screener.md:22-27`) | **Lost at the publication boundary**: single path coerces any non-INCLUDE to `EXCLUDE` (`collector.py:639`); partition sends any non-INCLUDE to `excluded` (`screening.py:479-484`); console API rejects `MAYBE`/`CONFLICT` with 422 (`console/api/screening.py:32, :48-54`) | Inspected code. The contract artifact can carry `MAYBE`, but nothing downstream honors it — the most consequential scientific-fidelity gap after row 5 | `PARTIALLY_ENFORCED` | §6 packet must not silently re-map: incomplete/unresolved batches fail closed (missing coverage ⇒ block); any future unresolved-publication rule needs an architecture decision (excluded from §6) | Deterministic test: a `MAYBE` decision file must not become a silent `EXCLUDE` in an authorized output without an explicit, recorded mapping |
| 10. Evidence locators, quotations, criterion references | Criterion codes partially present: `matched_inclusion_criteria` / `violated_exclusion_criteria` (`screening.py:17-28`), checklist booleans → deterministic decision (`calibration.py:65-120`, `collector.py:623-632`) | No locator/quote fields exist on either screening-decision model (`models.py:583-617`; `screening.py:17-28`); `screening_reasoning` / `reason` are free text; checklist booleans are transformed into code lists and the original booleans are **not** stored in `ContractDecision` | Inspected code + models. A false-anchor rejection test is currently inexpressible — there is nothing to verify against | `PARTIALLY_ENFORCED` | §6 packet: preserve the submitted per-criterion checklist alongside (not inside) the frozen `ContractDecision` — proposed as a linked record requiring an architecture decision (see §5); no generic envelope | N/A for §6 beyond asserting checklist preservation round-trips byte-identically |
| 11. Valid source anchoring vs valid interpretation | Skills separate them ("a locator proves location, not entailment"; `doer-contract:3`; critic axis 3, `critic-contract:10-18`); claims models separate `lexical_support` / `entailment` / `trust` (`models.py:97-122, :258-266`) | **No runtime check in the screening path**: batch carries title/abstract only, no source-text retention, no quote matching | Inspected code (negative result). The separation exists in claims-layer models, not in screening decisions | `DECLARED_ONLY` | None in §6 (screening operates on title/abstract metadata; full-text anchoring belongs to extraction, excluded) | `UNVERIFIED` for any claim that screening "validates evidence" — it does not in the inspected path |
| 12. Doer/critic separation and independence | Independence required by `doer-contract` ("do not open the peer artifact…", `:20-22`) and `screener.md:26`; critic non-repair required (`critic-contract:8`, `screening-critic.md:14`) | **No technical prevention found**: all three role prompts grant `edit: allow` (`screener.md:9`, `screening-critic.md:9`, `adjudicator.md:9`); the working-tree `reviewer.md` additionally grants `edit: allow`/`bash: allow` while its body claims read-only (`reviewer.md:1-13`) — direct contradiction, unrepaired per task rules. Peer files are filesystem-readable; nothing stops pre-completion inspection | Inspected prompts + `src/` grep (no permission-enforcement code found). The committed `HEAD` reviewer frontmatter (`edit: deny`, `bash: ask`) is the baseline-clean state; the working tree weakens it | `DECLARED_ONLY` (with an active working-tree contradiction) | Smallest runtime-independent repair belongs to the permission owner (revert `reviewer.md` to the baseline-clean frontmatter), **not** to the §6 packet; §6 must assume hostile-or-curious agents and gate at collection | Re-read `reviewer.md` frontmatter after any revert; no test can assert host-level permission enforcement from this repo |
| 13. Disagreement and adjudication lineage | Compass §3 ("dual screening requires two provenance-complete parent decisions; disagreement requires adjudication referencing both"); collector dual rules (`collector.py:370-396`, consensus `:398-420`) | Dual path enforces: both decisions required (`:370-373`), provenance completeness (`:322-358`), exact parent-set match for adjudication (`:388-396`), deterministic `COMPOSED` consensus IDs (`:401-410`). Single path: `parent_decision_ids` default `[]` (`:676`) | Inspected code. Do not conflate with `reconcile_multi_screener_decisions` majority voting (`screening.py:783-856`, incl. unadjudicated-tie fallback to `EXCLUDE`, `:844`) — the collector's dual rule is **unanimity-or-adjudication**, a stricter, different rule | `ENFORCED_IN_INSPECTED_PATH` (dual path) / `NOT_APPLICABLE` (single path) | None; §6 packet must preserve dual semantics unchanged | `tests/test_screening_migration.py` dual/adjudication cases (read, not executed) must be executed by the §6 packet's lane |
| 14. Model, skill, and execution provenance (incl. honestly-unavailable metadata) | `ContractDecision.model_id` / `prompt_version` optional (`models.py:591-592`); `MethodProvenance` enum (`:81-87`); calibration checklist determinism (`calibration.py:65-120`) | Passthrough is real (`collector.py:355-356, :701-702`); `method` defaults to `LLM` (`:674`), `decided_at` to `1970-…` (`:670`), `reviewed_by` to `agent-unknown`/`agent-legacy` (`batcher.py:165-183`) — unavailable metadata is **explicitly labeled**, never invented (a genuine strength). Gap: prompt text/skill version is not pinned in the inspected path; heuristic-fallback recommendations can carry `method: LLM` by default | Inspected code | `PARTIALLY_ENFORCED` | §6 packet: require `method` to be explicit (no silent default) on the authorization record's inputs; contract-model change excluded | Deterministic test: decision file without `method` is either labeled `UNKNOWN`-honestly or rejected — per the architecture decision in §6 |
| 15. Audit records and failure outcomes | Canonical vocabulary: `ARTIFACT_ACCEPTED`/`ARTIFACT_REJECTED` with actor, inputs/outputs, hashes (`contracts/acceptance.py:202-229, 574-588`); console `SCREEN_DECISIONS` (`console/api/screening.py:145-153`); append-only writer (`workspace/audit.py:144-210`); failure codes (Packet C reference §"Failure vocabulary"); typed refusals (`VerificationIdentityRefused`, `verification_identity.py:51-67`) | Acceptance + console audit writes are runtime-real. Gap: collector's own refusal branches (missing batch, membership failure, dual blocks) emit logger lines + exceptions, with a journal row only when `accept_artifact` was invoked (rejection record) — a refusal that never reaches `accept_artifact` leaves no journal row in the inspected path | Inspected code | `PARTIALLY_ENFORCED` | §6 packet: the authorization gate's allow/refuse outcomes must each emit a canonical journal event (reuse `workspace/audit.py:append_event`) | Assert journal row exists for both authorized-publication and refused-publication outcomes |
| 16. Retry, duplicates, concurrency, overwrite prevention | Idempotent retry gated by context+lineage (`acceptance.py:340-351, :478-529`); `IDEMPOTENCY_CONFLICT` on same-ID/different-payload (`:344-351`); `ORPHAN_ARTIFACT_PATH` (`:537-551`); atomic temp+replace with registry rollback (`:552-613`); `prepare` no-overwrite guard (`batcher.py:204-213`); `.rejected` renames + `MANIFEST` status correction (`collector.py:766-785`) | Real for artifact-level retry/overwrite. Gaps found in inspected path: (a) **duplicate study entries within one decisions file silently last-win** (`s1_map[…] = r`, `s2_map[…] = r`, `collector.py:294-295, :309-310` — no duplicate detection); (b) **no concurrency control** (lock/lease) found for concurrent reviewers writing the same `batch_NNN_decisions.json` | Inspected code (both gaps are negative results scoped to `screening/` + `acceptance.py`) | `PARTIALLY_ENFORCED` | §6 packet includes (a): reject duplicate study entries fail-closed. Concurrency leases are excluded (future work) | Deterministic tests: identical retry ⇒ idempotent accept; conflicting retry ⇒ `IDEMPOTENCY_CONFLICT`; duplicate-in-file ⇒ reject |
| 17. Fail-closed collection and publication | "Missing screening decisions must not silently produce included/excluded sets" (Compass §3); collector raises on missing/invalid/rejected (`collector.py:787-796`); verification-identity refusal raises pre-publication (`:152-181`); acceptance never publishes on failure (`acceptance.py:511-519`) | Real for **accepted artifacts and partition gating**. Gaps: (a) **no full-coverage check** — membership is validated one direction only (entries ⊆ candidates, `:592-598`); a file covering 1 of 20 candidates is acceptable to the inspected code (`ScreeningDecisionsData` requires ≥1 decision, `models.py:622`); console API likewise rejects unknown ids but not missing ids (`console/api/screening.py:115-130`). (b) Partition/publication outputs are plain files with no acceptance record | Inspected code | `PARTIALLY_ENFORCED` | §6 packet includes (a): exact-coverage gate (every candidate exactly once) before acceptance; plus authorization-before-legacy-publication (§6) | Deterministic tests: incomplete file ⇒ block + no `included.json`/`excluded.json` written; unrelated-file side effects asserted absent |

## 5. Vocabulary and model reuse

**Existing meanings (observed, not proposed).**

| Term | Meaning in the inspected code | Layer |
|---|---|---|
| `accepted` | `AcceptanceResult.accepted` + registry entry + `ARTIFACT_ACCEPTED` event (`acceptance.py:95-106, :574-588`). Conflates technical validity **and** publication: an accepted artifact is published by construction | Technical validity + publication |
| `validated` | Pydantic model validation + context/parent/binding checks inside `accept_artifact` (`:285-476`). No human judgment involved | Technical validity only |
| `reviewed` | Critic `PASS`/`FAIL`/`FAIL_ESCALATE` (`critic-contract:19-23`); console `reviewed_by` is merely a free-string attribution (`console/api/screening.py:84`), **not** this | Scientific review (declared gate; no runtime gate before collect) |
| `adjudicated` | Dual-path final `ContractDecision` with `parent_decision_ids == {s1, s2}` (`collector.py:380-396`) or `COMPOSED` consensus (`:398-420`). A third scientific judgment with lineage — not an authority grant | Scientific judgment + lineage |
| `refused` / `blocked` | `ARTIFACT_REJECTED` + `audit/rejections/<hash>.json` (`acceptance.py:170-229`); `VerificationIdentityRefused` codes (`verification_identity.py:29-36`); collector `RuntimeError` blocks (`:787-796`); doer `BLOCKED_INPUT`/`BLOCKED_STALE_PARENT`/`NOT_MY_SCOPE` | Technical refusal (must stay separate from scientific `MAYBE`/`CONFLICT`) |

**Why no flat status enum.** The code already demonstrates the failure mode:
`ScreeningDecisionValue` mixes a decision (`INCLUDE`/`EXCLUDE`) with workflow
states (`MAYBE`/`CONFLICT`), the console `Decision` model accepts only the
terminal two, and `partition_screening_results` re-derives a third uncertainty
channel from `confidence` (`0.40–0.70` ⇒ `conflicts`). Three overlapping
channels, three different coercions (§4 row 9). A flat enum would repeat this.
Required instead: **independent properties** — (i) technical validity
(acceptance result), (ii) scientific judgment (decision value, unresolved
preserved), (iii) authorization (separate record with identity + timestamp +
exact input hashes), (iv) publication (registry path + event). The existing
`ArtifactEnvelope` + `ContractDecision` already carry (i), half of (ii), and
(iv); (iii) is the missing piece and is exactly the §6 packet.

**Recommendation vs decision metadata.** The envelope provides artifact
identity, workspace/run/protocol/corpus binding, `inputs`, and producer
package/version/commit. `ContractDecision` adds `decision_id`, `study_id`,
`screener_id`, `method`, `decision`, `reason`, `decided_at`, optional
`model_id`/`prompt_version`, and `parent_decision_ids`. Actually missing for a
recommendation that must stay separable: (a) the per-criterion checklist as
submitted (booleans are destroyed by the transform, §4 row 10); (b) reviewer
authority (no model, §4 row 7); (c) an authorization reference on the published
side. (a) can be preserved as a **linked, byte-identical sidecar**; (b)–(c) are
one narrow **authorization record**. Both are proposals requiring an
architecture decision — **no new generic agent-output envelope is designed
here**, and none is needed: the existing envelope + decision models stay
frozen, with linkage by hash.

**Uncertainty vocabulary stays protocol-driven.** The doer skill already
requires it (`doer-contract:7`: "use only protocol/schema vocabulary… concepts
come from the workspace contract, not this skill"). Nothing in §6 imposes
intervention/outcome/domain requirements on reviews.

## 6. Recommended next packet (one bounded step)

**AG-01 — Authorization boundary for screening publication (proposal, requires
architecture decision).**

- **User-visible behavior.** After agents write `batch_NNN_decisions.json`,
  `collect` accepts each batch's `screening_decisions` artifact exactly as
  today (**recommendations**, unchanged semantics), but writes
  `included.json` / `excluded.json` / `conflicts.json` / PRISMA reports **only
  when** a valid authorization record for the exact recommendation hashes is
  present. Without it, collection stops after the accepted recommendation
  artifacts + a canonical refusal event — agent output is never again
  publishable as a scientific decision by accident. Deterministic defects
  (incomplete coverage, duplicate entries, out-of-batch ids, stale parents)
  are rejected with the same fail-closed discipline regardless of
  authorization.
- **Reuse.** `accept_artifact` + registry (`contracts/acceptance.py`),
  batch/binding/candidate checks (`screening/collector.py:211-281, :580-611`),
  wrapper provenance (`batcher.py:165-183`), append-only audit
  (`workspace/audit.py:append_event`), console membership check
  (`console/api/screening.py:105-130`), checklist derivation
  (`scholar_agent/calibration.py` + `collector.py:620-632`).
- **Owner paths.** `src/scholar_harness/screening/collector.py`,
  `src/scholar_harness/console/api/screening.py` (only if the authorization is
  writable via console), `tests/test_screening_authorization.py` (new),
  `docs/architecture/agent_control_enforcement_map.md` (this map, for the
  decision record). **No toolkit repository affected** — the boundary is
  harness-owned; no `tools/` change, no `plugins.json` pin change, no
  `nexus_scholar_pins.json` regeneration (established from the inspected code:
  all touched surfaces are harness-owned).
- **Explicit exclusions.** No contract schema/model change (frozen
  `ContractDecision` untouched; checklist preserved as linked sidecar only);
  no extraction, synthesis, model routing, scheduler, or agent platform; no
  mandatory-critique gate; no concurrency leases; no unresolved-state
  publication rule (unresolved still fails closed); no UI work; no baseline
  regeneration.
- **Required architecture decisions.** (1) Authorization record shape and home
  (journal event + file? registry-linked sidecar?) and which existing actor
  vocabulary supplies identity (do not invent a PKI here). (2) Whether `method`
  may still default or must be explicit at the authorization boundary (§4 row
  14). (3) Checklist-sidecar linkage format (hash-pinned, byte-identical).
  (4) Interaction with dual-path consensus (is `COMPOSED` consensus still a
  recommendation until authorized? — recommended: yes).
- **Delivery lane.** `RELEASE`: the packet changes publication behavior for an
  authoritative-adjacent output (`included.json` and friends gate downstream
  PDF/RAG stages). Per Compass §7 / `test_gate_policy.md`, publication
  behavior is always `RELEASE`, with `pr` + `closure` evidence and independent
  review/tester.
- **Acceptance tests (meaningful, small).** Deterministic-anchor tests (reject
  missing/false structure): incomplete decisions file ⇒ `RuntimeError`, no
  outputs written, prior outputs untouched; duplicate study entries ⇒ reject;
  out-of-batch id ⇒ reject + `.rejected` rename (existing behavior, now also
  without authorization); stale/fingerprint-mismatched parent ⇒ reject;
  identical re-collect ⇒ idempotent. Authorization tests: no authorization
  record ⇒ recommendations accepted, publication refused + refusal journal
  event; valid authorization ⇒ publication + `ARTIFACT…`-style journal event
  naming exact input hashes; authorization for different hashes (post-override
  file) ⇒ refused. Scientific-evaluation tests (do **not** conflate with the
  above): sampled critic review of whether a real quotation supports an
  exclusion — human-scored, reported separately, never asserted by the
  deterministic suite.
- **Remaining uncertainties / prerequisites.** Authorization UX and identity
  source (decision 1 above); legacy debt: existing recommendation files lack
  coverage/authorization lineage and must be classified, not backfilled;
  `BLOCKED_BASELINE_DRIFT` working-tree item should be reverted by its owner
  before any `RELEASE` candidate (it weakens the reviewer control the lane
  depends on); `tests/test_screening_migration.py` and
  `tests/console/test_console_screening.py` must be **executed** under the
  packet (they were read only for AG-00).

## 7. Unresolved questions

1. Who is an authorized approver in vocabulary the workspace already owns
   (human screen-credential? workspace role? console identity?) — needed before
   AG-01 test (authorization-valid) can assert anything real.
2. Should the authorization record live in the artifact registry (typed,
   accepted) or as a journal-anchored sidecar (lighter, no contract change)?
   The map recommends the lighter option but the decision is architectural.
3. What is the migration story for legacy `included.json`/`excluded.json`
   already published without authorization lineage — label as legacy debt or
   re-authorize?
4. Does the dual-path `COMPOSED` consensus need a distinct authorization quorum
   (two screeners already), or the same single authorization as the
   single-screener path?
5. Where should per-criterion checklists be preserved so they survive as audit
   evidence without touching the frozen decision model — and for how long?
6. Is any concurrency control (leases, single-writer) actually needed for
   `batch_NNN_decisions.json`, or is last-writer-wins + hash-pinned
   authorization sufficient given adjudication exists for the dual path?

---

*Observed facts* are cited by file:line at the inspected commit `1c4255e`.
*Interpretations* are the assessment statuses in §4. *Proposals* are the
"smallest missing behavior" cells, §5's linkage note, and §6 — all marked as
requiring architecture decisions, none implemented.
