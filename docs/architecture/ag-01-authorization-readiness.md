# AG-01 — Authorization Boundary for Agent-Assisted Screening Publication: Readiness and Enforceability Design

```yaml
task: AG-01-authorization-readiness
delivery_lane: FAST
owner_repo: nexus-scholar-org/nexus-scholar-harness
base_sha: d07100f39a94a750bbc858da4cb8638543486762
head_sha: 53b5e9878b9de86ab334a2549cb0b9c80c0e518d
branch: cdx/ag-01-authorization-readiness
allowed_paths:
  - docs/architecture/ag-01-authorization-readiness.md
  - tests/test_ag01_screening_authorization_characterization.py
  - docs/architecture/ag-02-screening-decision-integrity-packet.md
  - docs/architecture/DEVELOPER_COMPASS.md (docs-only link row, no semantic change)
immutable_boundaries:
  - docs/architecture/contract_v1_baseline.json (never regenerate to bless drift)
  - src/scholar_harness/contracts/** (frozen Contract v1; read-only for AG-01)
  - src/** behavior (no production change in AG-01)
  - tools/** (no kit change; no pin change)
  - workspaces/** (no real workspace mutation; tmp_path only)
  - .opencode/agent/** (no permission/frontmatter change)
  - primary-checkout dirty baseline (preserved, never absorbed/reverted/committed)
acceptance_ids: [AG01-WORKTREE, AG01-BRANCH, AG01-QUESTIONS, AG01-TABLE,
  AG01-CONTRACT, AG01-TEMPWS, AG01-GATE, AG01-PR]
open_findings: [AG-03-authorization-identity-source-unresolved]
known_baseline_failures: []
evidence:
  - command: uv run pytest tests/test_ag01_screening_authorization_characterization.py -q
    commit: 53b5e9878b9de86ab334a2549cb0b9c80c0e518d
    result: PASS (7/7)
  - command: uv run pytest tests/test_screening_migration.py tests/console/test_console_screening.py tests/test_contract_acceptance.py tests/test_contract_artifact_chain.py -q
    commit: 53b5e9878b9de86ab334a2549cb0b9c80c0e518d
    result: recorded in §8
  - command: uv run python scripts/generate_contract_baseline.py --check (+schemas, fixture, pins)
    commit: 53b5e9878b9de86ab334a2549cb0b9c80c0e518d
    result: recorded in §8
  - command: uv run ruff check scripts/ + git diff --check
    commit: 53b5e9878b9de86ab334a2549cb0b9c80c0e518d
    result: recorded in §8
  - command: uv run pytest tests/test_screening_decision_integrity.py -q
    commit: 86a9478b26f62de59c1cff9d233d9d6b84449b2b
    result: PASS (12/12); workflow-integrity (tamper-evidence + fail-closed), not authorization
  - command: uv run pytest tests/test_screening_migration.py tests/console/test_console_screening.py tests/test_contract_acceptance.py tests/test_contract_artifact_chain.py -q
    commit: 86a9478b26f62de59c1cff9d233d9d6b84449b2b
    result: PASS (36/36: 7 migration + 9 console + 11 acceptance + 9 chain), files unmodified
  - command: uv run pytest tests/test_ag01_screening_authorization_characterization.py -q
    commit: 86a9478b26f62de59c1cff9d233d9d6b84449b2b
    result: 4/7 PASS, file unmodified; 3 fail-closed by design (coverage-incomplete, duplicate, MAYBE-coercion demonstrations now refuse collection as AG-02 specifies)
  - command: uv run python scripts/generate_contract_baseline.py --check + generate_contract_schemas.py --check + generate_two_study_contract_fixture.py --check + generate_nexus_scholar_pins.py --check; uv run ruff check scripts/; git diff --check
    commit: 86a9478b26f62de59c1cff9d233d9d6b84449b2b
    result: PASS (all green; no contract/schema/fixture/pin drift)
  - command: uv run pytest -q --tb=no (full harness suite, PR gate, once)
    commit: 86a9478b26f62de59c1cff9d233d9d6b84449b2b
    result: 1181 tests, 1178 passed, 6 skipped, 3 failed -- the 3 failures are the AG-01 gap demonstrations above, now refusing collection by AG-02 design; zero other failures
next_gate: pr (design PR, fork-to-origin, no merge)
stable_sources:
  - docs/architecture/agent_control_enforcement_map.md@primary-untracked (AG-00 §§2-6; absent from base — see §0)
  - docs/architecture/agent_controls_decision.md@primary-untracked (see §0)
  - docs/architecture/agent_controls_plan.md@primary-untracked (see §0)
  - docs/architecture/DEVELOPER_COMPASS.md@d07100f (§1 WP-01 CLOSED_WITH_RESIDUAL_DEBT, §§2-3, §5, §7)
  - docs/architecture/agent_context_protocol.md@d07100f (capsule above)
  - docs/architecture/harness_core_modularity_roadmap.md@d07100f (§§1-7; has no §8 at base — see §0)
  - src/scholar_harness/screening/batcher.py@d07100f (full read)
  - src/scholar_harness/screening/collector.py@d07100f (full read)
  - src/scholar_harness/screening/report.py@d07100f (full read)
  - src/scholar_harness/agent_screen.py@d07100f (full read)
  - src/scholar_harness/console/api/screening.py@d07100f (full read)
  - src/scholar_harness/pipeline/screening_prepare.py@d07100f (HCM-04f delta)
  - .agents/skills/doer-contract/SKILL.md@d07100f
  - .agents/skills/critic-contract/SKILL.md@d07100f
  - .agents/skills/workspace-manager/SKILL.md@d07100f
```

**Status:** design/readiness ADR. No runtime behavior is changed by this
document. No authorization system is implemented here.

**Verdict (summary):** `BLOCKED_AUTHORITY_MODEL` is issued for **AG-03
authorization** — no enforceable human-approval mechanism exists in the
current local execution model, and none is invented here. A **bounded AG-02
integrity packet** (`ag-02-screening-decision-integrity-packet.md`) is issued
in parallel for **workflow-integrity only** (immutable batch binding, content
hashing, typed stale/replay refusal), with explicit non-claims: it cannot
distinguish agent bytes from human bytes and must never be described as
authorization. §4 states the exact limitation and the smallest realistic
alternatives.

## 0. Input provenance note (read this first)

Four governing inputs exist **only as uncommitted untracked files** in the
primary checkout (`d04f76f`) and are **absent from the canonical base**
`d07100f` used for this worktree:

- `docs/architecture/agent_control_enforcement_map.md` (AG-00, base `1c4255e`)
- `docs/architecture/agent_controls_decision.md`
- `docs/architecture/agent_controls_plan.md`
- `docs/architecture/inception_recon_scientific_review.md`

They were read once from the primary-checkout paths (read-only; the primary
checkout was not modified — see §8) and are cited below as
`@primary-untracked`. Their absence from `origin/main` is itself a provenance
fact: until those files merge, canonical `main` contains **no** AG direction,
**no** §8 in the HCM roadmap (the worktree roadmap ends at §7), and **no**
agent-control vocabulary. This ADR does not merge, restate-as-canonical, or
repair any of them; AG-00 remains historical assessment evidence per the
decision doc.

## 1. Refreshed AG-00 delta at the new base (`d07100f`)

### 1.1 What moved under HCM (between `1c4255e` and `d07100f`)

`1c4255e` is an ancestor of `d07100f` (verified via `git merge-base`). The
diff between the two SHAs touches **none** of these paths:

- `src/scholar_harness/screening/` (batcher, collector, report)
- `src/scholar_harness/agent_screen.py`
- `src/scholar_harness/console/api/screening.py`
- `src/scholar_harness/contracts/`
- `.opencode/agent/`

The screening-relevant HCM addition is one new adjacent file:

- `src/scholar_harness/pipeline/screening_prepare.py` (HCM-04f, 130 lines):
  a verbatim move of orchestrator Stage-4 preparation. It calls `cmd_prepare`
  at call time, counts `batch_*.json`, and writes the IN PROGRESS PRISMA
  note. By its own preservation notes it **emits no decisions, no collect
  output, and no audit event of its own; never imports the collector; never
  reads `included.json`** (`screening_prepare.py:35-40`). It adds no new
  authorization surface and no new publication path.

The remaining HCM diff (pipeline stages, orchestrator delegation, TD-E3
currentness decision/tests, stage unit tests) does not touch the screening
handoff. **AG-00 §§3–5 therefore hold verbatim at `d07100f` for the
prepare → recommendation → collect → publication path**, with the
re-verifications in §1.2.

### 1.2 What still holds (re-verified at `d07100f`, not merely carried)

| AG-00 finding | Re-verification at `d07100f` |
|---|---|
| Role prompts/frontmatter are declared conventions, not harness-enforced authorization | Re-verified: `src/` grep for permission/frontmatter enforcement returns only PDF-YAML and Obsidian-vault meanings; zero hits for `.opencode/agent` permission gating. Frontmatter at base: `reviewer.md` is `edit: deny` / `bash: ask` (baseline-clean); `screener.md`, `screening-critic.md`, `adjudicator.md` are `edit: allow` / `bash: ask`. |
| Single-screener collect is a 1:1 technical transform with no independent authorization | Re-verified: `collector.py:541-775` mints one `ContractDecision` per submitted entry (`:663-706`), accepts via the unchanged `accept_artifact` gate (`:752-770`), then partitions to `included.json`/`excluded.json` (`:810-836`). No authorization input, record, or check exists anywhere in the function. Executed proof: `test_publication_happens_with_no_authorization_record_anywhere`. |
| Critic gate is `DECLARED_ONLY` | Re-verified: `cmd_collect(workspace_dir)` signature admits no critique input; `screening-critic.md` + `critic-contract` gate text exists with no runtime counterpart. Executed proof: `test_collect_takes_no_critique_input_and_needs_none`. |
| `reviewer.md` working-tree permission weakening carried as drift | **Changed status — resolved in favor of the base, not repaired.** The weakening (`edit: allow` / `bash: allow` contradicting the read-only body) exists only in the primary checkout's uncommitted working tree. Canonical `d07100f:.opencode/agent/reviewer.md` is `edit: deny` / `bash: ask` = the AG-00 recorded-clean state. This worktree does not contain, absorb, or repair the primary's dirty hunk. The permission-mismatch control is still carried in §3 row 10 as a live control because the *class* (frontmatter says one thing, host grants another) is unenforceable from this repo regardless of the current frontmatter text. |
| Free-string identity with honest fallbacks | Re-verified unchanged: `batcher.py:165-183` (`agent-unknown` / `agent-legacy` / `1970-01-01T00:00:00+00:00`); `collector.py:671-674` (`screener_id` falls back to `reviewed_by`, `method` defaults to `LLM`); console `reviewed_by` defaults to `"console"` (`console/api/screening.py:84`). Executed proof: `test_forged_reviewed_by_string_is_accepted_as_screener_identity`, `test_console_decisions_body_accepts_any_reviewed_by_string`. |
| Membership-gated but coverage-incomplete; duplicates last-win/accepted; MAYBE coerced | Re-verified unchanged: one-direction membership (`collector.py:588-611`, console `:115-130`); no coverage check (`ScreeningDecisionsData` requires ≥1 decision, `models.py:622`); duplicate acceptance in single path; `decision = "INCLUDE" if raw == "INCLUDE" else "EXCLUDE"` (`collector.py:639`); partition sends non-INCLUDE to excluded (`screening.py:479-484`); console rejects MAYBE/CONFLICT with 422 (`console/api/screening.py:32,48-54`). Executed proofs: `test_coverage_incomplete_file_is_accepted_today`, `test_duplicate_study_entries_are_accepted_today`, `test_maybe_decision_is_silently_coerced_to_exclude_today`. |
| Immutable parent binding + stale/cross-workspace refusal enforced | Re-verified unchanged: prepare fingerprint equality (`batcher.py:231-236`); registry-resolved parents, never the handoff (`collector.py:216-221,580-583`); `accept_artifact` context/parent/binding checks; fail-closed raise with no outputs (`collector.py:787-796`). Existing executed coverage: `test_collect_rejects_decisions_outside_parent_batch`, `test_prepare_fails_closed_on_protocol_fingerprint_mismatch`, `test_screening_decisions_must_match_registered_batch` (acceptance suite). |

### 1.3 Baseline state of this worktree

`generate_contract_baseline.py --check` result is recorded in §8. No
baseline file was regenerated; no contract, schema, fixture, or pin file was
touched. The worktree diff is limited to the four allowed paths (§8).

## 2. The six mandatory questions (with evidence + limitation each)

### Q1 — Who approves a screening decision for publication?

**Answer: nobody — no approver identity exists in the harness.** The only
approver-shaped fields are free strings: `reviewed_by`
(`batcher.py:165-183`, console default `"console"` at
`console/api/screening.py:84`) and `screener_id`
(`collector.py:671-673`, `models.py:586` requires only `min_length=1`).
There is no approver registry, no role-to-permission mapping, no login or
session, and no key material anywhere in the inspected path.

**Limitation:** any design that reads `reviewed_by`/`screener_id` as
approval is a forgery-accepting design (executed proof: forged
`"professor-x"` collects and publishes). AG-03 must introduce an identity
source the harness controls (see §4 alternatives); until then, "who"
is unanswerable and publications are unattributed recommendations.

### Q2 — What exactly is approved (which bytes, which binding)?

**Answer: today nothing is approved; recommendations are transformed.**
The accepted `screening_decisions` artifact binds workspace, run,
protocol/corpus fingerprints, parent batch artifact id+sha
(`collector.py:727-750`), and minted decision ids — but its *inputs* are
whatever bytes the decision file contained at collect time. No hash of the
recommendation bytes is recorded, so "the exact content that was reviewed"
is not a harness concept yet.

**Limitation:** without a recorded input hash, post-hoc substitution is
undetectable from the registry. AG-02 closes exactly this (record the
decision-file sha256 in lineage; refuse changed-bytes re-acceptance) **as
tamper-evidence, not as approval** — a hash says *which bytes*, never *who
authorized them*.

### Q3 — Where is the boundary enforced (which code, on every path)?

**Answer: the only funnel is `cmd_collect`, and it enforces technical
validity only.** File path (`agent_screen.py collect`), console path
(`POST /api/v1/screening/batch/{n}/decisions` writes the same
`batch_NNN_decisions.json`), and orchestrator path (HCM-04f delegates to
`cmd_prepare`; collection stays behind the same `cmd_collect`) all converge
on `collector.py:99-836`. Enforcement present at the funnel: parent-batch
resolution from the registry (`:211-244, :580-583`), one-direction
membership (`:246-281, :588-611`), `accept_artifact` acceptance
(`:529-538, :752-770`), verification-identity bridge-or-refuse (`:152-181`),
fail-closed raise before partition (`:787-796`).

**Limitation:** the funnel sees bytes, not actors. Any path that writes the
decision file bypasses nothing — but also proves nothing about who wrote
it. A UI-only or console-only approval would be bypassed by the file path
(rejected alternative, decision doc item 5); the check must live in shared
harness services used by all paths.

### Q4 — What are the honest host assumptions (trusted local researcher)?

**Answer (decision doc item 4, adopted):** the design targets a **trusted
local researcher and a bounded agent interface**, explicitly NOT protection
against an administrator with arbitrary filesystem access. The harness runs
as the same OS user as the agent; files the human can write, the agent can
write.

**Limitation:** under these assumptions, *no file-based approval record is
unforgeable*. A signed-approval file, a hash-pinned manifest, or a
`reviewed_by` string are all bytes the agent can mint. Enforceable
separation requires something outside the shared filesystem: a console
operator action the agent process cannot invoke (see §4), host-provided
identity (OS user, SSH-agent key, hardware token), or an out-of-band
signature against a key the agent cannot read. If none is available, the
pilot must report the isolation limit, not claim enforced separation.

### Q5 — Is the boundary provider-neutral (no model/skill identity as authority)?

**Answer: the boundary must be, and today trivially is, provider-neutral —
because it authenticates nothing.** `model_id`/`prompt_version` are
optional passthrough (`collector.py:355-356,701-702`,
`models.py:591-592`); `method` defaults to `LLM` even for heuristic
fallbacks (`collector.py:674`).

**Limitation:** neutrality cuts both ways. Preserving real provenance
(actual model, skill version, calibration) is AG-02/AG-03 lineage work, but
no model string, confidence score, `requires_human_review` flag, or critic
verdict may ever confer authority (decision doc item 2). Neutrality means
the gate treats all recommendation sources identically: unapproved until a
human approval mechanism exists.

### Q6 — How are scientific decisions protected (uncertainty, coverage, lineage)?

**Answer: partially at the model layer, lost at the publication boundary.**
`ScreeningDecisionValue` preserves MAYBE/CONFLICT (`models.py:90-94`) and
dual-path lineage preserves `[s1, s2, final]` (`collector.py:422-426), but:
single-path collect coerces non-INCLUDE to EXCLUDE (`:639`); partition
repeats the coercion; console rejects MAYBE/CONFLICT outright; incomplete
coverage publishes silently; duplicates are accepted.

**Limitation:** these are **integrity** defects, fixable deterministically
(AG-02), and must not be confused with **authorization**. Fixing coercion
and coverage still leaves the Q1 gap untouched: a complete, well-formed,
all-INCLUDE agent file would publish — correctly-shaped, but still an
unapproved recommendation.

## 3. Enforceability table (folded AG-01 matrix — no second file)

Status vocabulary (AG-00 §4, unchanged): `ENFORCED` = runtime code rejects
or gates in the inspected path (executed where a test name is cited);
`PARTIAL` = part gated, part not; `DECLARED` = stated in skill/prompt/doc
with no runtime gate; `ABSENT` = neither declaration nor gate where
inspected. "Trusted actor/authority source" names the party whose honesty
the control depends on. No row claims what its limitation denies.

| # | Control | Threat prevented | Enforcement point | Trusted actor / authority source | What an untrusted agent can still do | Testable invariant | Honest limitation |
|---|---|---|---|---|---|---|---|
| 1 | Unauthorized decision-file creation / replacement | Silent injection or overwrite of screening recommendations | **None on the agent-file path** (`ABSENT`); atomic temp+replace + membership check on the console path only (`console/api/screening.py:92-95,105-130`, `PARTIAL` overall) | Filesystem owner (host OS), not the harness | Create, overwrite, or delete any `batch_NNN_decisions.json` before `collect`; forge any `reviewed_by` string | Forged `reviewed_by="professor-x"` collects and publishes with `screener_id` verbatim (`test_forged_reviewed_by_string_is_accepted_as_screener_identity`) | No writer authentication exists; AG-02 hash-recording makes overwrite *detectable after the fact*, never *impossible*. Overwrite prevention requires host file ownership the harness does not have. |
| 2 | Wrong-batch file (batch index mismatch) | Decisions applied to the wrong candidate set | Console: 400 on body/path batch disagreement (`:109-110`); agent-file path: filename selects the batch, membership re-checked per file at collect (`collector.py:588-611`) (`ENFORCED` at collect, `PARTIAL` at write) | Accepted parent batch artifacts (registry) | Write a correctly-shaped file for any batch index, including batches assigned to another screener | Out-of-batch study ids rejected + file renamed `.rejected` (existing `test_collect_rejects_decisions_outside_parent_batch`) | Filename is convention; the real binding is candidate-set membership, which AG-02 tightens to exact coverage. Batch-index confusion between two valid batches with overlapping ids is not detectable — ids are batch-scoped only via the registry parent. |
| 3 | Changed protocol/corpus after prepare | Screening against stale criteria or a stale study set | `cmd_prepare` fingerprint equality refuses (`batcher.py:231-236`, `sys.exit(1)`); collect re-binds to registry parents (`collector.py:580-583,752-756`) (`ENFORCED`) | Accepted corpus snapshot + `protocol.json` bytes at prepare time | Mutate `protocol.json` or `verified.json` *after* prepare: prepare-time binding already fixed the accepted parents, so collect still screens the old candidates (correct), but the human-readable `batch_NNN.json` protocol summary is now stale text | Protocol tamper ⇒ `test_prepare_fails_closed_on_protocol_fingerprint_mismatch`; stale-parent acceptance refused (`test_screening_decisions_must_match_registered_batch`) | The handoff file's embedded protocol summary is unaudited display text; the enforced binding is fingerprint-to-artifact, not text-to-text. |
| 4 | Out-of-batch study IDs | Smuggled studies entering the PRISMA counts | One-direction membership vs the accepted parent candidate set, both paths (`collector.py:588-611`; console `:122-130`) (`PARTIAL` — see row 5 for the missing direction) | Accepted parent batch artifact candidate set | Submit unknown ids only if *all* entries are unknown — still rejected; but omit candidates freely (row 5) | Spoofed id ⇒ `.rejected` + `RuntimeError` + no outputs (existing `test_collect_rejects_decisions_outside_parent_batch`) | Membership proves "was a candidate", not "was assigned to this screener", and says nothing about completeness. |
| 5 | Content changed after approval ("approval" = any prior collect) | Old acceptance validating new bytes | **Content hash not recorded today** (`ABSENT`); artifact identity is deterministic on content, so changed content mints a *different* artifact rather than reusing the old acceptance (`collector.py:716-726`) (`PARTIAL` by accident of determinism, not by check) | Deterministic id derivation (`contracts/canonical.py`) | Overwrite the file and re-collect: a new artifact is accepted with no link to, or refusal citing, the superseded one | AG-02 invariant (new): re-collect with bytes differing from the recorded decision-file hash ⇒ typed `CONTENT_CHANGED` refusal, with both hashes in the journal; identical bytes ⇒ idempotent accept | Hash-recording detects substitution only if the registry/jounal entry it is compared against is itself intact — a filesystem-privileged adversary can rewrite history (row 11). Tamper-evidence, not tamper-prevention. |
| 6 | Duplicate / replayed decisions | Double-counted studies; replayed file accepted as fresh work | **No duplicate detection** (`ABSENT` — dual path dicts last-win `:294-295,309-310`; single path appends all); idempotent retry only at the artifact-acceptance layer (`IDEMPOTENCY_CONFLICT` on same-id/different-payload) (`PARTIAL`) | `accept_artifact` idempotency for byte-identical retries | Submit the same study twice (accepted today); replay an old file under a new batch filename (membership decides, not freshness) | Duplicates accepted today (`test_duplicate_study_entries_are_accepted_today`); AG-02 invariant (new): duplicate study entries per screener ⇒ fail-closed refusal; exact-bytes re-collect ⇒ idempotent, no new artifact | Cross-batch replay of *valid-for-that-batch* content is indistinguishable from legitimate re-screening without a freshness anchor; AG-02 anchors freshness to the parent batch artifact sha, not to wall-clock time (no trusted clock is assumed). |
| 7 | Stale approval after new batch (re-prepare) | Decisions collected against a superseded run | `prepare --force` guard exists for batches (`batcher.py:204-213`) but protects batch files, not decision freshness (`PARTIAL`); run binding is deterministic on fingerprints, so identical inputs re-mint identical ids (idempotent, not stale) | Registry run/batch lineage | Re-collect old decisions after a re-prepare with identical inputs: silently idempotent (arguably correct); after *changed* inputs, membership/binding refuses (correct) — the gap is only the *silent* cases with no recorded decision-file hash | AG-02 invariant (new): collect refuses when the decision file's batch binding (run id + batch artifact sha) does not match the current registry head for that batch index — typed `STALE_BINDING` refusal | "Current" is defined as registry head; if the registry itself is rolled back at the filesystem level, staleness detection rolls back with it (row 11). |
| 8 | Agent claiming human-approved | Forged authority laundering agent output into "human decisions" | **No gate** (`ABSENT` — the exact center of `BLOCKED_AUTHORITY_MODEL`) | None exists | Set `reviewed_by` to any human name, set `method` to `HUMAN`, backdate `decided_at` — all accepted as strings | Forged HUMAN-method file publishes as human-attributed output (extension of the `professor-x` characterization: `method` is equally free, `collector.py:674`) | AG-02 and any integrity work **must not** treat `method: HUMAN` or a human-like `reviewed_by` as approval. Tests must assert the opposite: human-*labeled* but unapproved files publish (pre-AG-03) exactly like agent-labeled ones. |
| 9 | Agent writing arbitrary workspace paths (`../escape`, extra files) | Registry/audit poisoning; collect consuming attacker-placed files | Collect reads a **fixed filename set** (`batch_{idx:03d}.json`, `*_decisions.json`, `MANIFEST.json`) under `literature/screening/`; parents resolve via registry artifact paths, never via decision-file contents (`collector.py:211-244,564-578`) (`ENFORCED` for collect-consumed paths; extra files are ignored, not policed) | Harness-fixed path construction (no path input from decision files) | Write extra files anywhere (ignored by collect, but visible to humans/tools); overwrite the mutable handoff `batch_NNN.json` display text (membership still checked against the registry artifact, so smuggled candidates still fail) | Path-fixed writer only (console `_batch_file`, `:88-89`); AG-02 keeps the fixed set and adds: unknown files under `screening/` are reported, never consumed | The harness cannot prevent writes — only refuse to *consume* them. Human operators must not treat stray workspace files as evidence. |
| 10 | Reviewer/critic permission mismatch (frontmatter says read-only, host grants edit) | Critic silently repairing the artifact it reviews; reviewer becoming an author | **No harness gate** (`DECLARED` — frontmatter is a host convention; `src/` contains no permission-enforcement code, re-verified §1.2) | The host (OpenCode permissions), never the harness | With `edit: allow`, open the peer artifact pre-completion, copy its answers, or rewrite the reviewed file — nothing in the harness detects it | No test *can* assert host-level enforcement from this repo (AG-00 row 12, unchanged); AG-02 asserts the harness-side complement: collection never consumes critique/critic files as decisions (fixed path set, row 9) | At base `d07100f` the committed `reviewer.md` is baseline-clean (`edit: deny`/`bash: ask`); the weakening is primary-working-tree-only and is not absorbed, repaired, or blessed here. Independence remains a procedural property, enforced by task packets and host config, not by the harness. |
| 11 | Host gives agent the same filesystem credentials as the human | All file-based distinctions between "agent wrote" and "human wrote" collapse | **No distinction exists** (`ABSENT` by architecture: single OS user, shared workspace) | The host OS / operator session — outside this repo | Do anything the human can do to workspace bytes: write decisions, rewrite the registry, append journal rows, re-prepare batches | Characterization invariant: two files with identical bytes but different authors are indistinguishable to every harness check (this is *why* AG-02 claims workflow-integrity only) | **Workflow-integrity ≠ OS-security.** AG-02 detects mistakes, staleness, and misuse *within* the workflow (loud refusal instead of silent corruption). It provides zero protection against a filesystem-privileged adversary, including an agent running with the operator's credentials. Claiming otherwise would be the fake security system this ADR refuses to build. |

## 4. Verdict: `BLOCKED_AUTHORITY_MODEL` (authorization) + bounded AG-02 (integrity)

### 4.1 The block

**`BLOCKED_AUTHORITY_MODEL` is issued for AG-03 authorization.** The exact
limitation: *in the current local execution model — one OS user, shared
workspace filesystem, no operator login/session, no approver registry, no
key material, free-string identity fields, host-convention-only role
permissions — there is no mechanism by which the harness can bind a
publication decision to an authenticated human approver.* Any
"authorization record" built from freely-writable JSON (a signed-looking
file, a hash-pinned manifest entry, a `reviewed_by` string, a console
`reviewed_by` default, a prompt-text instruction, or a role label) is
forgeable by the same agent it purports to constrain, and shipping it as
"authorization" would manufacture precisely the false certainty the Compass
forbids ("do not invent provenance", §3; "make the evidence chain
trustworthy before making the agents more autonomous", §12).

The six AG-00 unresolved questions that require an identity source (AG-00
§7 Q1–Q2 especially) remain open and are **not** answered by assertion
here.

### 4.2 Smallest realistic alternatives (in ascending order of strength)

1. **Explicit HITL procedure without crypto claims (available now,
   weakest, honest).** A documented operator runbook: the human reviews
   `batch_NNN_decisions.json` diffs, runs `collect` themselves, and the
   journal records the operator's shell session as the actor. Provides
   *deterrence and audit trail*, not enforcement — an agent with shell
   access can perform the same steps. Cost: near zero. Claim allowed:
   "operator-attended run", never "authorized publication".
2. **Console confirmation at collect (small runtime, AG-03 scope).**
   Require a human click/keypress in the local console process to release
   partition outputs, with the console process bound to the operator's
   desktop session (not reachable from the agent's shell). Raises the bar
   from "write a file" to "drive the operator's UI session". Still
   bypassable if the agent shares the session (stated limitation), and the
   file/CLI path must refuse publication without the console release —
   otherwise it is theater. Cost: one shared-service gate + bypass tests.
3. **Host-provided authenticated identity (requires host support).** The
   host injects an operator identity the agent process cannot mint: OS-user
   separation (agent runs as a different UID with write access only to
   `*_decisions.json`), an SSH-agent/hardware-token signature over the
   exact decision-file hash, or an MCP/OAuth operator session passed to the
   console. The harness verifies (pubkey/UID/session) rather than trusts a
   string. Cost: deployment + identity plumbing outside this repo; the
   harness side is a verifier for an externally-supplied credential.
4. **Externally-supplied signed approval (strongest, most machinery).**
   The human signs (batch, decision-file sha256, policy version, timestamp)
   with a key held outside the agent's reach; the harness verifies the
   signature against a pinned trust root before AG-03 collection. Replay,
   cross-batch, and stale-signature refusal become cryptographic rather
   than conventional. Cost: key management, trust-root distribution, and
   revocation — a project of its own; do not build a bespoke PKI inside
   the harness.

Until one of 2–4 is selected **and its enforcement demonstrated by test**
(plan AG-C10: "or the pilot explicitly reports that enforcement requirement
as unmet"), AG-03 runtime work stays blocked, and every publication from
`collect` remains a technically-accepted recommendation, not an authorized
scientific decision.

### 4.3 What is NOT blocked: bounded AG-02 integrity

A real, testable mechanism **does** exist for workflow-integrity, because
`cmd_collect` is a single harness-controlled funnel that can refuse loudly
instead of publishing silently. The bounded packet
`docs/architecture/ag-02-screening-decision-integrity-packet.md` implements
**only**: immutable batch binding, decision-file content hashing, exact
coverage, duplicate rejection, unresolved-refusal, and typed stale/replay
refusal — with explicit non-claims (no identity, no approval, no
agent-vs-human distinction). This is the decision doc's item 5 ("resolve
deterministic integrity defects first") and does not depend on, or wait
for, an identity source.

## 5. AG-02 / AG-03 boundary (normative for both packets)

| Concern | AG-02 (integrity — packet issued) | AG-03 (authorization — BLOCKED until §4.2) |
|---|---|---|
| Exact coverage, duplicate rejection, unresolved-refusal | Yes: deterministic gates on (parent artifact, submitted file) | Reuses; unchanged |
| Decision-file sha256 recorded in lineage + journal | Yes: tamper-evidence | Reuses as the *content* side of approval binding |
| Typed stale/replay refusal (`STALE_BINDING`, `CONTENT_CHANGED`, duplicate, incomplete) | Yes, registry-anchored | Reuses refusal vocabulary for stale approvals |
| Who approved, approver registry, operator session, signatures | **Excluded** — no such concept is introduced | Required; blocked on §4.2 alternative selection |
| Gating `included.json` publication on approval | **Excluded** — publication semantics unchanged | The AG-03 behavior change (RELEASE lane) |
| `method: HUMAN` / human-like `reviewed_by` as authority | Explicitly **not** trusted (row 8) | Replaced by the selected identity mechanism |
| Dual-path consensus/adjudication semantics | Preserved byte-for-behavior | `COMPOSED` consensus remains a recommendation until approved (decision doc item 4; AG-00 Q4 carries) |

Anti-corruption rules for AG-02 (from the plan's warning): AG-02 must not
be described, labeled, or tested as an authorization guarantee; AG-03/04
completeness requires the whole approved path demonstrated, not separate
PRs each claiming partial isolation.

## 6. How OpenCode subagents participate safely without becoming approvers

- **Screener** (`screener.md`, `edit: allow`): produces recommendations at
  exactly the assigned `batch_NNN_decisions.json` path (doer-contract
  invariants 1, 6: don't touch another agent's output; write only the
  assigned path). Its output is *input* to the funnel, never authority.
  Knowledge cutoff / model identity is provenance metadata, not approval.
- **Screening-critic** (`screening-critic.md`): writes only the assigned
  critique artifact (critic-contract: never repair the reviewed artifact).
  A critic PASS is a review signal for the human operator; `cmd_collect`
  cannot see it by construction (§2 Q3), so it can neither approve nor
  block — matching its `DECLARED_ONLY` status honestly.
- **Adjudicator**: resolves explicitly assigned disagreements with
  `parent_decision_ids == {s1, s2}` lineage (collector dual path). A third
  scientific judgment with lineage — not an authority grant (AG-00 §5
  vocabulary: `adjudicated` ≠ authorized).
- **Reviewer** (`reviewer.md`, baseline `edit: deny` / `bash: ask`):
  adversarially reviews diffs/artifacts; never edits, never approves by
  implication. The AG-01/AG-02 PRs themselves go through this reviewer —
  review of the *mechanism*, not approval of *scientific decisions*.
- The harness never inspects subagent role labels, frontmatter, or prompt
  text when deciding what to accept: authority-relevant properties must be
  runtime-checkable at the funnel. "The agent said it is the reviewer" is
  row-8 forgery with a different costume.

## 7. How humans retain final responsibility

1. Until AG-03 unblocks, **no harness output is an authorized scientific
   decision**, regardless of `method` labels or attribution strings.
   Operators must treat `included.json`/`excluded.json`/PRISMA reports as
   technically-validated recommendation partitions — downstream PDF/RAG
   stages consume *evidence*, not verdicts.
2. The human's responsibility is discharged through *actions outside the
   agent's forgeable surface*: reviewing diffs, running collection in an
   attended session, and (once selected) performing the §4.2 approval
   action with a credential the agent cannot mint.
3. Legacy outputs stay legacy: existing recommendation files and
   previously published partitions lack coverage/authorization lineage and
   must be classified as unverified, never backfilled with retroactive
   actors or timestamps (decision doc items 5, 9; Compass §9 "do not invent
   provenance").
4. Uncertainty stays the scientist's: MAYBE/CONFLICT are preserved as
   unresolved through AG-02 (refuse-to-finalize) so that no human is ever
   presented with a silently completed exclusion as "the harness's
   decision".

## 8. Ownership, audit, and validation evidence

- **Toolkit sync:** no toolkit change. No `tools/**` edit, no
  `plugins.json` `default_rev` bump, no `nexus_scholar_pins.json`
  regeneration. No canonical kit repo affected — harness-only design track.
  (If any kit change appears necessary during AG-02, the packet requires
  STOP + `BLOCKED_CANONICAL_REPO` instead of a vendored patch.)
- **Workspace audit:** no real workspace state change; all behavioral
  evidence uses synthetic `tmp_path` workspaces. No `journal.jsonl` write;
  N/A with reason recorded here per the packet.
- **Scope discipline:** no `src/` behavior change (read-only inspection);
  no contract/fixture/schema regeneration; no `.opencode/agent`
  permission change; primary-checkout dirty baseline preserved (verified
  unchanged before/after — see validation below); no auth runtime, OAuth,
  RBAC, UI, provider integration, or synthesis code.
- **Validation (FAST lane, worktree only):** exact commands, exit codes,
  and summaries:
  - `git status --short` (worktree): shows only the four allowed-path
    additions/modification; `git rev-parse HEAD` + `git log --oneline -3`
    pin the evidence SHA in the capsule.
  - Primary checkout `git status --short` re-run at close: must match the
    §0 baseline exactly (no new files, no absorbed hunks).
  - `uv run pytest tests/test_ag01_screening_authorization_characterization.py -q`:
    PASS 7/7 (executed behavioral evidence for §§1–3).
  - `uv run pytest tests/test_screening_migration.py -q`,
    `tests/console/test_console_screening.py -q`,
    `tests/test_contract_acceptance.py -q`,
    `tests/test_contract_artifact_chain.py -q`: existing ownership suites
    stay green (no drift introduced by a docs+tests-only diff).
  - `uv run python scripts/generate_contract_baseline.py --check`,
    `generate_contract_schemas.py --check`,
    `generate_two_study_contract_fixture.py --check`,
    `generate_nexus_scholar_pins.py --check`: contract/pin consistency.
  - `uv run ruff check scripts/` + `git diff --check`: whitespace/lint.
- **Delivery:** branch `cdx/ag-01-authorization-readiness`, fork→PR to
  `nexus-scholar-org/nexus-scholar-harness` base `main`, merge-ready, never
  merged. Max 3 coder-reviewer cycles.
