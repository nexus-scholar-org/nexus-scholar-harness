# Test Suite Audit (read-only, FAST lane)

Status: audit only. No policy, framework, contract, pin, permission, code, test, or CI change made. Cleanup proposals are unimplemented.

Sections 1–10 retain the original audit baseline. The dated addendum below
updates completed-task evidence without turning historical observations into
current-state claims.

- Baseline SHA: `a6eda074f14dcd3c4688ea3f9187b3d4a556b63c` on `main` (`origin/main` in sync).
- Delivery lane: FAST. No suite run, no install/sync, per packet.
- Dirty baseline: `M .opencode/agent/reviewer.md` (edit deny→allow, bash ask→allow) — PRESERVED and excluded from all conclusions.
- AG-03C: Queued per [agent_controls_plan.md](agent-controls/agent_controls_plan.md); no branch, no open PR, no delivery evidence. Excluded from completed-work findings.
- UAV task: provisional pilot only (PR #123 merged 2026-10-13T10:32Z; `validation.json` PROVISIONAL_NOT_FROZEN; synthetic 3 positive / 6 negative refused; no search/screening executed). Used for research-friction findings only.
- Scope rule: findings describe committed `main` only. Candidate-branch observations are labelled as such and never combined with merged revisions into one measurement.

## 1. Scope and evidence sources

Governing sources already read: [AGENTS.md](../../AGENTS.md), [DEVELOPER_COMPASS.md](DEVELOPER_COMPASS.md), [test_gate_policy.md](test_gate_policy.md), [test_gate_manifest.json](test_gate_manifest.json), [agent_context_protocol.md](agent_context_protocol.md), pull-request-gate skill, CI config, `tests/conftest.py`, `scripts/select_test_gate.py`.

Static evidence (no execution): ~80 test files, ~1016 test functions (parametrized count higher), ~34125 lines under `tests/`. PR #121 executed the full harness suite (1264 passed / 6 skipped) plus authority 85/85. PR #122 (docs-only) also ran the full suite plus authority 85/85 despite runtime being unchanged. CI job wall-times of ~1m22s–1m45s (`gh run list`) measure env+wheel work, not the suite: the `lint-and-test` job in [.github/workflows/ci.yml](../../.github/workflows/ci.yml) does not run pytest — only ruff on `scripts/`, installer `--help`, manifest validation, pins `--check`, wheel build+smoke, and a best-effort plugin install. Suite wall-time is therefore MISSING; this report labels it honestly and manufactures no timing.

## 2. Verdict: size, quality, gate frequency

- Size: large but not shown to be slow — suite time unmeasured. No count-based quality claim; no reduction target set.
- Quality: authority and contract-boundary coverage is genuinely protective (see §5). Maintenance-cost hotspots are assertion style (exact strings, layout bytes), not test count.
- Gate frequency: the demonstrated waste is repeated full-gate execution on changes that cannot affect runtime (PR #122), plus a double wheel build in CI. First savings should come from gate narrowing, not test deletion.
- Net assessment: keep every regression-protection outcome; reduce how often the heaviest gates run on changes that cannot affect them, and reduce how brittlely outcomes are asserted. Nothing in this audit weakens a contract, authority, or pin guarantee.

## 3. Audit questions

**Q1 — Validation-time split (env vs suite).** CI time observed (~1m22s–1m45s) covers environment sync, lint, manifest/pins checks, wheel build+smoke, and wheel-e2e. The harness pytest suite does not run in CI at all, so no env-vs-suite split can be computed from CI logs. Suite wall-time: MISSING (no execution in FAST lane). Maintenance burden (§3 Q3) is tracked separately from execution time and must not be conflated with it.

**Q2 — Distinct-outcome map.** Similar names are not duplicates. Authority files guard distinct behaviors: review lifecycle (snapshot/supersession/refusal/derived-binding), approval binding (operator-identity/scope/policy/revoke/expiry/atomicity), Windows-MIC isolation windows, disposable accept→snapshot→mint→promote plus six negatives, AG-01 gap evidence, AG-02 fail-closed screening, E4 six-mutation fail-closed proof. No two files were found to assert the same outcome on the same input; removal candidates in §4 name retained coverage explicitly.

**Q3 — Maintenance cost (concrete locations).** Highest-cost style is exact-string `==` assertions: `tests/authority/test_review_lifecycle.py:266`, `tests/authority/test_isolation_windows.py:318`, `tests/mcp/test_mcp_setup.py:110`, `tests/recon/test_engine.py:245`, `tests/unit/test_hydration_stage.py:330/390/410/543`. Next is doc-layout byte coupling: `tests/unit/test_screening_prepare_stage.py:374/412/502/521/607/970`, `tests/unit/test_extraction_stage.py:318`, `tests/unit/test_synthesis_stage.py:425`, `tests/unit/test_graph_stage.py:362/656`. Private-import coupling (`tests/e2e/test_extraction_runtime_acceptance.py:252/2113/2284`, `tests/conformance/test_mcp_tool_parity.py:16`, `tests/conformance/test_e2_extraction_boundary.py:1979`, `tests/recon/test_gates.py:13`, `tests/console/test_console_pipelines.py:172/180`) is a coupling cost, not an execution cost.

**Q4 — Gate efficiency (log-supported only).** Demonstrated repetition (1 occurrence, PR #122): docs-only change ran the full harness suite (1264 passed / 6 skipped) plus authority 85/85 with runtime unchanged — the same gate PR #121 ran for a runtime change. Demonstrated structural repetition (every CI run): the wheel is built twice ([ci.yml](../../.github/workflows/ci.yml) `lint-and-test` step and `wheel-e2e` step) with entrypoint smoke in the first and the P7.8 uvx flow in the second. No other repetition counts are log-supported; no frequency is extrapolated.

**Q5 — AG-03C proportionality (conditional).** No AG-03C evidence exists yet, so no proportionality assessment of 03C can be made. For merged AG-03A/B, the authority suites listed in §5 are proportionate regression protection and must stay. When 03C lands, approval, currentness, coherent-generation, crash/race/retry, and audit-failure coverage must be retained at full strength; simplification of 03C-adjacent tests without weakening those guarantees is the only acceptable shape.

**Q6 — Research friction (lighter dev checks).** UAV provisional friction (from PILOT_EVALUATION.md + `validation.json`, provisional scope only) suggests inner-loop checks (gate selection probe, single-file targeted test, `git diff --check`) carry the iteration, while full-suite and wheel-e2e gates stay at PR/closure. Accepted-artifact integrity (frozen inputs, adjudication lineage, provenance events) is never the thing being lightened — only the repetition frequency of heavy gates on unchanged runtimes.

## 4. Prioritized findings (each with required 7 fields)

Overview — highest leverage first, safest first:

| ID | Area | Action | Touches tests? |
|----|------|--------|----------------|
| F1 | Docs-only full-gate repeat | NARROW GATE | No |
| F2 | Double wheel build in CI | CONSOLIDATE | No |
| F3 | Unmapped areas fall back to full suite | REWRITE (manifest) | No |
| F4 | Exact-string assertions | REWRITE (pilot) | Yes, behavior-preserved |
| F5 | Layout-byte assertions | REWRITE (pilot) | Yes, behavior-preserved |
| F6 | Private-import coupling | KEEP | No |

**F1 — Full suite + authority re-run on docs-only change (PR #122).**

- Location: gate selection for docs-only PRs (policy: [test_gate_policy.md](test_gate_policy.md), selector: `scripts/select_test_gate.py`).
- Protected behavior: full regression confidence for runtime changes.
- Redundancy/cost evidence: PR #122 ran 1264 passed / 6 skipped + authority 85/85 with runtime unchanged (same gate as PR #121). Log-supported count: 1 occurrence.
- Suggested action: NARROW GATE — route docs-only diffs to manifest/pins/link checks, keep full suite for runtime diffs.
- Coverage that must remain: full suite + authority gates for any `src/`, `tools/`, `tests/`, or packaging change.
- Risk + confidence: low risk; high confidence the PR #122 run was redundant (runtime-unchanged premise is log-supported).
- Later verification: record gate selection on the next docs-only PR; confirm full suite skipped and checks green.

**F2 — Wheel built twice per CI run.**

- Location: [.github/workflows/ci.yml](../../.github/workflows/ci.yml) `lint-and-test` build step vs `wheel-e2e` build step, with entrypoint/E3 smoke in the first and P7.8 uvx flow in the second.
- Protected behavior: wheel smoke (P7.7 lazy-import gate) and uvx portability flow (P7.8 gate).
- Redundancy/cost evidence: two builds of the same metapackage wheel per run; structural (every CI run), not timed — no minutes claimed.
- Suggested action: CONSOLIDATE — share one built artifact between jobs if the release workflow permits; else KEEP with rationale recorded.
- Coverage that must remain: both smoke gates (entrypoint `--help` + E3 import probe + uvx e2e) must still execute per run.
- Risk + confidence: low-medium risk (artifact passing across jobs touches release plumbing); medium confidence without timing data.
- Later verification: CI log showing single build feeding both smoke steps, or a written decision to keep two builds.

**F3 — Manifest covers only T-10..T-150; authority/pipeline/unit/e2e-E4/console/mcp/recon fall back to the full suite.**

- Location: [test_gate_manifest.json](test_gate_manifest.json) `tasks` vs `fallback` (harness fallback is the full suite).
- Protected behavior: correct gating for mapped RAG/agent/harness-E3/pins/skills tasks.
- Redundancy/cost evidence: unmapped areas always take the heaviest gate by construction; no per-area timing exists, so this is structural, not measured waste.
- Suggested action: REWRITE (manifest extension, implementation work — not a test change): add read-only mappings for unmapped areas; fallback stays until each mapping is proven.
- Coverage that must remain: full-suite fallback for every unmapped path until its mapping lands and passes review.
- Risk + confidence: low risk (additive mappings only); high confidence the gap exists (manifest inspection).
- Later verification: selector output for an authority-only diff shows a targeted gate; fallback still triggers for unknown paths.

**F4 — Exact-string assertions couple tests to message bytes.**

- Location: `tests/authority/test_review_lifecycle.py:266`, `tests/authority/test_isolation_windows.py:318`, `tests/mcp/test_mcp_setup.py:110`, `tests/recon/test_engine.py:245`, `tests/unit/test_hydration_stage.py:330/390/410/543`.
- Protected behavior: refusal wording, isolation outcomes, setup contracts, recon engine messages, hydration semantics.
- Redundancy/cost evidence: static style evidence only — any message rewording breaks these without a behavior change. No failure-frequency data; no duplicate-outcome claim.
- Suggested action: REWRITE (pilot on one file): normalize or match on stable substrings/codes while keeping one exact-match assertion per behavior where wording is contractual.
- Coverage that must remain: the protected behavior above, asserted at least as strongly (same inputs, same outcomes).
- Risk + confidence: medium risk in authority files (wording may be contractual); medium confidence. Authority rewrites need reviewer sign-off.
- Later verification: targeted test file passes; a deliberate rewording probe fails only the intended contractual assertion.

**F5 — Doc-layout byte assertions couple stage tests to rendering.**

- Location: `tests/unit/test_screening_prepare_stage.py:374/412/502/521/607/970`, `tests/unit/test_extraction_stage.py:318`, `tests/unit/test_synthesis_stage.py:425`, `tests/unit/test_graph_stage.py:362/656`.
- Protected behavior: stage output structure and content completeness.
- Redundancy/cost evidence: static style evidence only — layout shifts break these without semantic change.
- Suggested action: REWRITE (pilot on one stage file): assert parsed structure/semantics over literal bytes.
- Coverage that must remain: semantic completeness of each stage output (no silent field loss).
- Risk + confidence: low-medium risk; medium confidence.
- Later verification: targeted stage tests pass; a whitespace-only rendering change no longer breaks them while a dropped-field mutation still fails.

**F6 — Private-import coupling in e2e/conformance/console/recon tests.**

- Location: `tests/e2e/test_extraction_runtime_acceptance.py:252/2113/2284`, `tests/conformance/test_mcp_tool_parity.py:16`, `tests/conformance/test_e2_extraction_boundary.py:1979`, `tests/recon/test_gates.py:13`, `tests/console/test_console_pipelines.py:172/180`, `tests/conformance/test_count_freshness.py:92`.
- Protected behavior: boundary and parity guarantees reached through internals.
- Redundancy/cost evidence: INSUFFICIENT EVIDENCE that a stable public surface exists for each import; coupling cost is real but removal would drop coverage.
- Suggested action: KEEP (no change now); revisit only alongside an explicit public-surface decision per area.
- Coverage that must remain: all current boundary/parity assertions stay until a public entry point covers them.
- Risk + confidence: high risk if removed now; high confidence KEEP is correct under insufficient evidence.
- Later verification: none required unless a public-surface proposal reopens this finding.

## 5. Protections that must remain (justified, not exhaustive)

- AG-03A approval binding (`tests/authority/test_approval_binding.py`, 402L/20defs): operator-identity, scope, policy, revoke, expiry, atomicity — historical failure tests, regression protection.
- AG-03B review lifecycle (`tests/authority/test_review_lifecycle.py`, 433L/19defs): snapshot/supersession/refusal/derived-binding — same justification.
- AG-02 fail-closed screening (`tests/**/test_screening_decision_integrity.py`, 627L/12defs) and AG-01 gap evidence (`tests/**/test_ag01*`, 463L/7defs).
- Contract/pins/count freshness: `test_contract_baseline.py` (58L/4defs), `test_nexus_scholar_pins.py` (198L/6defs), `test_count_freshness.py` (138L/5defs) — byte-identity and SHA guarantees must not be loosened for convenience.
- E4 negative proof (`tests/**/test_e4_negative_proof.py`, 961L/10defs): six mutations fail-closed; shared fixtures in [tests/conftest.py](../../tests/conftest.py) (E2E_ANSWERS, ScriptedResponder, sample fixtures, tmp_workspace) stay.
- Disposable flow (`tests/**/test_disposable_flow.py`, 556L/12defs): accept→snapshot→mint→promote plus six negatives — lifecycle atomicity must keep an end-to-end negative path.
- Isolation windows (`tests/authority/test_isolation_windows.py`, 318L/9defs, 15 cases): Windows-MIC Low-vs-Medium separation — platform-gated assertions stay even where exact-string style (F4) is later softened.
- Wheel and skills gates (`tests/**/test_nexus_scholar_metapackage.py`, 89L/5defs; `test_select_test_gate.py`, 70L/6defs): 11 wheel entries, entrypoints, 14 skills, and T-10..T-150 selection behavior stay pinned.
- For AG-03C (when it lands): approval, currentness, coherent-generation, crash/race/retry, and audit-failure coverage must remain at full strength.

## 6. Cleanup sequence (safest first)

1. F1 gate narrowing for docs-only diffs (no test touched).
2. F3 manifest extension for one unmapped area with fallback intact (no test touched).
3. F2 single-build consolidation or recorded keep-decision (CI plumbing only).
4. F5 pilot rewrite on one stage file (test-only, semantics preserved).
5. F4 pilot rewrite on one non-authority file first; authority files last with review.
6. F6 stays KEEP until a public-surface decision exists.

## 7. Unresolved questions and limits

- Suite wall-time is unmeasured (FAST lane ran no suite); no before/after timing claim is possible until a STANDARD lane records it.
- Per-file maintenance frequency (which brittle assertions actually break) has no log support — style risk only.
- Shared-fixture extraction (e.g. a `tests/pipeline/conftest.py`) is hypothesized, not evidenced; `tests/conftest.py` contents were not inventoried beyond the packet's fixture list.
- Oversized fixtures (`e3_golden_manifest.json` 150L/5856B, `e4_golden/` 30 files, `e1_vendored` 2 files) are noted but not costed — INSUFFICIENT EVIDENCE for action.
- `release.yml`/`publish.yml` build-without-smoke asymmetry is out of FAST scope; flagged for a later gate-consistency pass, not decided here.
- Committed-main vs candidate-branch discipline: PR #121/#122 bodies and `gh run` timings are candidate-branch execution evidence used only for gate-frequency (Q4), never merged into static main-branch findings. AG-03C has neither, so it contributes no finding at all.
- This audit ran no pytest, no ruff beyond `git diff --check`, and no installs; any line below that reads like a measurement without a cited log is a hypothesis by construction (see §8).

## 8. Established vs hypotheses vs implementation work

- Established (committed-main evidence): PR #122 redundant full run; double wheel build structure; manifest T-10..T-150 gap with full-suite fallback; brittle assertion locations; AG-03C Queued with no evidence; UAV provisional scope.
- Hypotheses (not actionable as findings): unmeasured suite time; which brittle assertions break most often; fixture-extraction savings; release/publish smoke asymmetry impact.
- Proposed implementation work (later tasks, not this audit): F1 gate-narrowing PR (§9); F3 manifest-extension task; F4/F5 pilot rewrites; any timing-measurement task under STANDARD lane. This report creates no policy, collection, or archive.
- What this audit does not do: change any gate threshold, weaken any schema/fixture/authority assertion, set a test-count reduction target, rank tests by count as quality, or authorize deleting regression protection. Every REMOVE-adjacent idea was converted to KEEP or NARROW GATE with retained coverage named.

## 9. First cleanup PR recommendation (bounded, gate-first)

Prefer redundant-gate elimination over test deletion: a docs-only gate-narrowing PR that routes diffs touching only documentation (no `src/`, `tools/`, `tests/`, packaging, workflow, or pin changes) to `git diff --check` plus manifest/pins/link validation, skipping the full harness suite and authority gates; any runtime-file presence restores the full gate. Verification is log-supported: the next docs-only PR's gate log shows the narrowed selection green, and the next runtime PR's log shows the full gate intact. No test file is added, removed, or weakened.

## 10. Evidence index

Policy and gates: [test_gate_policy.md](test_gate_policy.md), [test_gate_manifest.json](test_gate_manifest.json), [agent_context_protocol.md](agent_context_protocol.md). Entry and plans: [AGENTS.md](../../AGENTS.md), [DEVELOPER_COMPASS.md](DEVELOPER_COMPASS.md), [agent_controls_plan.md](agent-controls/agent_controls_plan.md). Execution and fixtures: [.github/workflows/ci.yml](../../.github/workflows/ci.yml), [tests/conftest.py](../../tests/conftest.py), `scripts/select_test_gate.py`.

## 11. Post-AG-03C addendum — 2026-10-13

Refresh baseline: committed canonical main `d5e824b85d57bfe61ae7719ad6103baaddd19b1b`.
The original `a6eda07` audit remains unchanged in scope; this is a documentation
refresh, not a new test audit or execution measurement.

- AG-03C is now merged: [implementation PR #125](https://github.com/nexus-scholar-org/nexus-scholar-harness/pull/125),
  candidate `db73597`, merge `2846066a6090085e2a8fa57bef0e9e417335f2a9`;
  [close-out PR #126](https://github.com/nexus-scholar-org/nexus-scholar-harness/pull/126),
  merge `d5e824b85d57bfe61ae7719ad6103baaddd19b1b`.
- PR #125 records **1313 passed, 6 skipped, 0 failed, 0 errors** for the full
  suite, and **128 passed** for authority tests, including 43 publication-generation
  cases. These are reported delivery evidence, not fresh runs by this audit.
- The orchestrator reports three full-suite measurements. Their individual
  commands, candidate SHAs and intervening executable changes have not been
  verified here; no additional redundant-run finding is established.
- Preserve authorization, coherent-generation, currentness, crash/race/retry
  and audit-failure protection. The Windows deployment claim remains bounded;
  POSIX is unproven and tmp+rename is not a filesystem-durability guarantee.
- The packet explicitly distinguishes true legacy (reported LEGACY_UNVERIFIED,
  bounded compatibility exception) from downgrade after authorized material
  (MISMATCHED refusal). The exception's retirement criteria need checking before
  describing all legacy consumers as protected; no bypass conclusion is made here.
- Sources: [AG-03C packet](agent-controls/ag-03c-publication-generations.md),
  the two PR bodies above, [PR #121](https://github.com/nexus-scholar-org/nexus-scholar-harness/pull/121)
  and [PR #122](https://github.com/nexus-scholar-org/nexus-scholar-harness/pull/122).
  The refreshed CI workflow still has two wheel builds and no pytest command.

**First cleanup remains F1.** Reconcile the contribution skill's unconditional
full-suite instruction with the existing policy's documentation-only reuse rule.
Classify changed surfaces conservatively: documentation consumed by tests,
generated artifacts, packaging or runtime is not automatically exempt. Select
lightweight checks relevant to the diff, preserve required boundary checks, and
keep the executable fallback. This addendum changes no policy or selector.

## 12. F1 implementation record — 2026-10-13 (merged PR #127)

F1 merged in PR #127 at `465c3861e906f47bb7470902b74f5ef63a8a94f4` (implementation baseline `ac8f270`):
selector `scripts/select_test_gate.py` classifies change sets
(`docs/architecture/test_gate_manifest.json` `docs` section: consumed boundary
map, locked patterns + drift gates); prose-only selects the light gate
(`git diff --check`, no suite); consumed docs keep `test_count_freshness.py` /
`sync_skills_bundle.py --check`; locked docs keep baseline + schemas `--check`;
executable paths keep mapped/fallback gates; unknown paths take the conservative
harness full suite; empty selection stays an error; the pull-request-gate skill
defers to `test_gate_policy.md` via the selector (no mirror exists).
Evidence: `tests/unit/test_select_test_gate.py` 17/17 green (F1-01..F1-09),
`select_test_gate.py --check` OK, baseline `--check` current, `ruff` clean.
F2–F6 remain open and unchanged.

After that bounded cleanup, continue AG-04. F2–F5 remain follow-ups; F6 stays KEEP.

## 13. Kit-test ownership clarification — 2026-10-13

Evidence: user-supplied read-only clarification at `ac8f270`, inspected against
the vendored kit test snapshots at that revision. This records that review;
it is not a fresh independent inspection or comparison with newer canonical
kit repositories. No suite, installation or dependency synchronization was run.

The 54/81 count is a text-reference inventory, not an ownership or dependency
map. It includes imports, monkeypatch targets, comments and architectural guards;
it misses indirect, shared-fixture and some CLI dependencies. The other 27 files
have **no kit reference detected by this scan**, not proven kit independence.

| Sample | Finding | Disposition |
|---|---|---|
| `tests/unit/test_http_client.py` | Search-kit retry/backoff behavior; equivalent coverage not found in inspected vendored tests | KEEP; deferred ownership-review candidate, not demonstrated duplication |
| `tests/unit/test_completeness.py` | Search-kit scoring behavior; merge-preservation tests cover a different outcome | KEEP; deferred ownership-review candidate, not demonstrated duplication |
| `tests/authority/test_publication_generations.py` | Harness authorization/generation behavior uses valid kit-produced parents | KEEP harness tests and per-test parent/corpus binding |
| `tests/unit/test_deduplication_stage.py` | Harness plumbing differs from kit algorithm tests | KEEP both integration and algorithm coverage |
| `tests/unit/test_pipeline_core.py` | Architectural dependency guard, not kit-domain behavior | KEEP guard and its non-vacuity checks |

**No genuine duplication was found in the inspected sample.** This is not a
suite-wide conclusion. Similar imports or exercised lines do not establish
equivalent inputs, outcomes and failure modes.

Repeated load/validate/fingerprint setup is a possible small helper extraction;
per-test corpus bytes and lineage assertions remain deliberate. Do not replace
valid kit-produced parents with hand-written objects merely to remove dependencies.
Consolidation is deferred until a concrete maintenance benefit is established.

**Decision approved by the user:** finish F1, then proceed to AG-04. This
clarification does not expand F1, authorize test deletion, or delay AG-04.
Later F3 work may map one executable area while retaining unknown-path fallback.

Deferred ownership probe (F3-O1): inspect canonical search-kit tests at a named
revision. If adopting the HTTP/completeness cases in the kit is useful, retain
the harness coverage until equivalent kit tests land and pin/vendor state is
synchronized. Any later slimming must retain harness integration checks and
include the kit tests in required validation. Kit/pin changes continue to require
cross-kit checks; moving a test must not remove it from release evidence.
