# Docs & Specs Consolidation Plan (2026-10-12)

**Status:** PHASES 1–4 + the archive purge EXECUTED 2026-10-12 (see §9 Execution
log). Phase 5 (contract-locked `.opencode` broken-link repairs) remains deferred —
it requires contract-baseline regeneration and an explicit version decision.

**Owner intent.** The `docs/` and `specs/` trees have accumulated stale
historical text and a newcomer finds them overwhelming. The active work is the
**WP** program (WP-01 delivered; remaining WP open) plus three tracks — **HCM**
(harness core modularity), **AG** (agent controls), **UI** (research-ui app).
Legacy material should be removed, merged, grouped, or archived away from the
live tree, while the **system architecture and the core indexes survive**.

**Scope of this plan:** `docs/` (93 files) and `specs/` (62 files), ~2.6 MB.

---

## 1. Problem statement (evidence)

Every scan confirmed the same root cause: **the indexes describe the pre-WP
Phase 0–7 era and never mention the current program.**

- `docs/architecture/README.md` indexes only `phase_*/` plus
  `harness_core_modularity_roadmap.md`. The **AG, HCM, and UI files sit loose in
  the `docs/architecture/` root, entirely unindexed.**
- `docs/README.md` indexes phases 0/5/6/7 and the user guide, but not
  `research_ui/`, `v1_specification/`, `v2_planning/`, `DEVELOPER_COMPASS.md`,
  `agent_control*`, `hcm_*`, `harness_core_modularity_roadmap`, `contract_v1*`,
  or `test_gate*`.
- `docs/UPCOMING_WORK.md` is a Phase-era roadmap mislabeled "Live"; it has no
  WP/HCM/AG/UI coverage.
- `docs/architecture/temp_analysis_archive/` (16 files) is **fully redundant**:
  `v1_specification/` is its consolidation (per-section `<!-- Source: … -->`
  tags).
- `docs/architecture/v2_planning/` (7 files) documents an abandoned V2 direction
  (raw LLM APIs / swarms) that contradicts the current agent-in-the-loop design.

---

## 2. Hard constraints — must not break

Each constraint was verified against the repo (glob / `rg` / `git log`).

| Constraint | Files | Consequence if moved/edited |
|---|---|---|
| **Contract-locked** — hashed by `scripts/generate_contract_baseline.py`, asserted by `tests/conformance/test_contract_baseline.py` | `docs/architecture/contract_v1_baseline.md`, `contract_v1_baseline.json`, `cross_kit_contract_v1.md`, `wp01_contract_adoption_handoff.md`, `wp01_packet_c_reference.md`; `specs/deep-audit-remediation-2026-09-17/10_cross_kit_contracts.md`, `12_execution_roadmap.md` | **Requires contract-baseline regeneration** + an architecture/version decision. |
| **Runtime-read by a test** | `docs/architecture/wp01_packet_e2_extracted_text_handoff.md` (read at `tests/conformance/test_e2_extraction_boundary.py:1900-1901`) | Moving requires editing that test in the same change. |
| **Runtime-read by a script** | `docs/architecture/test_gate_manifest.json` (read by `scripts/select_test_gate.py`) | Moving breaks the gate selector. |
| **CI count-asserted** | `docs/kits_surface_matrix.md` (referenced by `tests/conformance/test_count_freshness.py` and 6 `.agents/**/SKILL.md`) | **Keep path.** Renaming breaks tests + skills. |
| **Published metadata URL** | `docs/nexus_scholar_user_guide.md` (referenced from `packaging/nexus-scholar/pyproject.toml` `Documentation` URL) | **Keep path** or update the published URL. |
| **Soft docstring/comment citations** (won't fail tests, repoint for correctness) | `docs/architecture/ag-01-authorization-readiness.md` (`tests/test_ag01_screening_authorization_characterization.py:4`), `hcm_04e_verification_identity_decision.md` (`tests/test_verification_identity_characterization.py:23`), `docs/architecture/research_ui/AGENT_WORK_PACKETS.md` (`apps/research-ui/components/primary-nav.tsx:9`) | Repoint on move; readability only. |

**Reassuring negatives (verified):** no `.github/` workflow and no `packaging/`
file references any `docs/`/`specs/` path; `docs/architecture/DEVELOPER_COMPASS.md`
contains **zero** `specs/` references. So the moves below break nothing
executable except the four special cases above.

---

## 3. Classification

### 3.1 DELETE — 28 files, ~10k lines, zero inbound references

Recoverable from git history if ever needed.

- `docs/architecture/temp_analysis_archive/` — **16 files** (redundant with
  `v1_specification/`).
- `docs/architecture/v2_planning/` — **7 files** (abandoned direction).
  *Optional:* retain only `v2_architecture_spec.md` for decision provenance.
- `docs/architecture/phase_0/05_cycle_a_contract_first.md` — superseded by
  Contract v1 / WP-00. **Correction (verified 2026-10-12):** the file is linked
  from `docs/architecture/phase_0/README.md:56`, so "zero refs" was wrong —
  deleting it requires dropping/updating that README row in the same change
  (or deleting it together with the `phase_0/` archive move in phase 3).
- `docs/architecture/e3_rag_chroma_recovery_capsule.md` — orphan; superseded by
  `e3_residual_repair.md`.
- `specs/archive/phase_f_specialized_agents/handoff_spec.md` — near-identical
  duplicate of the live `specs/handoff/handoff_spec.md`.
- `specs/archive/phase_f_specialized_agents/schemas.py` — orphan `.py` file in a
  docs tree; no imports anywhere.
- `docs/internal/review_prompts/review_prompt_inception_sweep.md` — zero-ref
  one-shot prompt for a completed sweep.

### 3.2 MERGE

| Source | Target | Note |
|---|---|---|
| `docs/UPCOMING_WORK.md` | `docs/ROADMAP.md` | Add a "Current program" section (WP/HCM/AG/UI); keep the Phase-era backlog as history. |
| `docs/architecture/wp01_e3_adoption_status.md` | E3 completion record (`wp01_packet_e3_completion_report.md` / `e3_residual_repair.md`) | 27-line stale "in progress" snapshot. |
| `docs/internal/audits/harness_vision_report.md` + `harness_vision_report-11.md` | `unified_harness_vision_report.md` | Two scoring passes folded into the canonical synthesis. |

*Optional (decide later):* `16_publication_strategy.md` ↔
`exploratory-grounding-agent/15_scientific_publication_plan.md` → `specs/publication/`;
`13_scientific_agent_loop_framework.md` + `14_…catalog.md` →
`specs/scientific-agent-loops/` (neither is contract-locked; only the two locked
files are hashed).

### 3.3 GROUP / MOVE

| Group | Target folder | Entrypoint | Members |
|---|---|---|---|
| **AG track** | `docs/architecture/agent-controls/` | `agent_controls_plan.md` | Active: plan, `agent_controls_decision.md`, `ag-03a-protected-publisher-feasibility.md`. Archive: `ag-01`, `ag-02`, `agent_control_enforcement_map.md`, `agent_layer_reassessment_2026-10-12.md`. |
| **HCM track** | `docs/architecture/harness-core-modularity/` | `harness_core_modularity_roadmap.md` | Current: `hcm_05_mcp_recon_adapter_characterization.md`. Archive: `hcm_01_characterization_packet.md`, `hcm_04e_verification_identity_decision.md`. |
| **UI track** | `docs/architecture/research_ui/` (keep) | `AGENT_WORK_PACKETS.md` | Keep as-is; **create the missing `README.md`** (see §5). |
| **WP packet archive** | `docs/architecture/wp01/` | (add `README.md`) | `wp01_packet_e1_*`, `e2_*`, `e3_*`, `e4_*` + `e3_residual_repair.md`. |
| **ADRs** | `docs/architecture/decisions/` | (add index) | `td_e3_currentness_decision.md` (orphan ADR). |
| **Legacy archive** | `docs/internal/architecture/` | — | `phase_0/` (5 files), non-live `phase_5/` (`README`, `BLUEPRINT`, `PLAN`, `COMPONENTS`), `phase_6/README.md`, `v1_specification/` → renamed `v1_analysis/`. |

### 3.4 STAY (live, do not move)

- `docs/architecture/`: `README.md`, `DEVELOPER_COMPASS.md`,
  `agent_context_protocol.md`, `test_gate_policy.md`, `test_gate_manifest.json`,
  and the **5 contract-locked** files.
- `docs/architecture/phase_5/SPECS.md` — live console + `PipelineSpec` contract
  (the only `phase_5/` file edited after the 2026-09-14 reorg).
- `docs/architecture/phase_7_distribution/README.md` — shipped distribution
  record (target of `AGENTS.md` and a conformance guard).
- `docs/kits_surface_matrix.md`, `docs/nexus_scholar_user_guide.md` — keep paths
  (see §2).
- All of `specs/deep-audit-remediation-2026-09-17/` — **this is the WP program**.
- `specs/inception-ecosystem/`, `specs/handoff/`, and the code-cited files in
  `specs/exploratory-grounding-agent/` (`13_evaluation.md`, `14_agent_loops.md`,
  `16_inception_improvements.md`, `03_lifecycle.md`, `04_memory_and_cache.md`,
  `README.md`).
- `specs/archive/**` — already grouped; only the two orphans in §3.1 leave.

---

## 4. Target tree

```
docs/
  README.md                      # REWRITTEN master index (covers current program)
  ROADMAP.md                     # ← UPCOMING_WORK.md merged + current-program section
  nexus_scholar_user_guide.md    # keep path (PyPI metadata URL)
  kits_surface_matrix.md         # keep path (CI count-asserted)
  architecture/
    README.md                    # + "Active tracks" table (WP / HCM / AG / UI)
    DEVELOPER_COMPASS.md
    agent_context_protocol.md
    test_gate_policy.md
    test_gate_manifest.json
    contract_v1_baseline.md      # LOCKED
    contract_v1_baseline.json    # LOCKED
    cross_kit_contract_v1.md     # LOCKED
    wp01_contract_adoption_handoff.md   # LOCKED
    wp01_packet_c_reference.md          # LOCKED
    agent-controls/              # + archive/
    harness-core-modularity/     # + archive/
    research_ui/                 # + README.md (new)
    wp01/                        # e1–e4 + e3_residual_repair + README
    decisions/                   # td_e3_currentness_decision.md
    phase_5/SPECS.md
    phase_7_distribution/README.md
  internal/
    README.md
    COMMIT_SNAPSHOTS.md
    audits/  ecosystem/  review_prompts/
    architecture/                # NEW archive root
      phase_0/  phase_5/  phase_6/  v1_analysis/
```

Proposed `docs/README.md` sections: (1) Start here — root `README.md`, user
guide, `DEVELOPER_COMPASS.md`; (2) **Current program** — WP / HCM / AG / UI table;
(3) System architecture — `architecture/README.md` + `v1_analysis/` pointer;
(4) Reference — `kits_surface_matrix.md`, `test_gate_*`, `COMMIT_SNAPSHOTS.md`;
(5) Archive — `internal/` + `architecture/{archive,decisions}`, marked
"historical, do not cite as current."

---

## 5. Content repairs (independent of moves)

- **`AGENTS.md` (root)** — "Active milestone: Phase 7" is stale; should name the
  current program (WP + HCM/AG/UI).
- **`phase_7_distribution/README.md` status contradiction** — README says
  "SHIPPED / all P7 `[x]`" (PRs #17–#32, PyPI live); `AGENTS.md` calls it the
  active milestone; `UPCOMING_WORK.md:60` leaves P7.9 unchecked. Reconcile.
- **Stale headers:** `specs/exploratory-grounding-agent/README.md` says
  "Proposal / Architecture Brainstorm" (contradicts "Implemented & Verified");
  `specs/deep-audit-remediation-2026-09-17/README.md` says "1.0.0-draft";
  `docs/architecture/hcm_01_characterization_packet.md` says "PREPARED; not
  completed" though its own §results record execution.
- **Broken links in contract-locked agent files:**
  `.opencode/agent/orchestrator.md` and `.opencode/agent/coder.md` cite
  `specs/deep-audit-remediation-2026-09-17/10_task_list.md` and
  `.../12_remediation_roadmap.md` — **neither exists** (the real file is
  `12_execution_roadmap.md`; there is no `10_task_list.md`). Both agent files are
  in `EXPLICIT_PATHS` ⇒ **requires contract-baseline regeneration**.
- **`docs/architecture/research_ui/README.md` does not exist** but is cited by
  `UI-01C_WORK_PACKET.md:6`, `UI-01D_WORK_PACKET.md:143`, and acknowledged in
  `UI-03_CONTEXT_CAPSULE.md:59`. Create it or drop the 3 refs.
- **`docs/architecture/inception_recon_scientific_review.md` is untracked** —
  commit it (referenced by AG-00 / AG-01) or it is lost on a clean checkout.

---

## 6. Proposed execution order

Each phase is its own branch → fork → PR (contribution gate).

1. **Zero-risk repairs** — create `research_ui/README.md`; commit the untracked
   `inception_recon_scientific_review.md`; fix the stale headers in §5. *(no
   moves)*
2. **Pure deletes** — the 28 files in §3.1 (≈ −10k lines, **zero link
   breakage**).
3. **Group / move** — §3.3 into the new folders; repoint all links, including
   the E2 conformance-test path and the rag-kit `SKILL.md` canonical + generated
   mirror.
4. **Indexes** — rewrite `docs/README.md` + `docs/architecture/README.md`; add
   `docs/ROADMAP.md`.
5. **Contract-locked repairs** — the `.opencode` broken links (§5); separate,
   with contract-baseline regeneration + a version decision.

Phases 1–4 are independent of the frozen contract and can ship without
regeneration. Phase 5 is gated on an explicit baseline-regeneration decision.

---

## 7. Open decisions

- Keep `v2_architecture_spec.md` alone, or delete all of `v2_planning/`?
- Take the optional `specs/publication/` and `specs/scientific-agent-loops/`
  merges?
- Legacy archive root: **`docs/internal/architecture/`** (chosen).
- Whether to fold the `UI-01C/01D_WORK_PACKET` files (executable supersets of
  `AGENT_WORK_PACKETS.md §UI-01c/01d`) into the UI spec, or leave them in
  `apps/research-ui/docs/`.

---

## 8. Evidence base

Five read-only scans over disjoint chunks (`docs/architecture/` WP+contract;
`docs/architecture/` AG/HCM/UI; `docs/architecture/` legacy dirs; the whole
`specs/` tree; `docs/` root + `docs/internal/` + repo-root docs). Method per
file: last-commit date (`git log -1 --format=%cs`), inbound references
(`rg -l` for relative path ∪ basename across `src/ tests/ scripts/ .agents/
.opencode/ .github/ packaging/` and other docs/specs), and a tracked/untracked
check. Constraints in §2 were confirmed against the actual scripts and tests,
not inferred. The §3.1 zero-ref claim, the E2 test path, the manifest reader,
and the PyPI URL were re-verified directly on 2026-10-12 before phase 1.

---

## 9. Execution log

### 2026-10-12 — phases 1–2 (branch `docs/consolidation-phase-1-repairs`)

**Phase 1 — zero-risk repairs (done):**
- `AGENTS.md`: stale "Active milestone: Phase 7" replaced with the current
  program (WP + HCM/AG/UI); Phase 7 recorded as shipped.
- `docs/architecture/research_ui/README.md`: **created** (cited by UI-01C/UI-01D
  but absent from every git revision — the predecessor was untracked and is
  unrecoverable; the new file says so and points at `I18N.md` for the i18n
  policy).
- `docs/architecture/inception_recon_scientific_review.md`: **committed**
  (previously untracked).
- Stale headers fixed: `specs/exploratory-grounding-agent/README.md`
  (Proposal → Complete/historical),
  `specs/deep-audit-remediation-2026-09-17/README.md` (1.0.0-draft → normative
  baseline), `docs/architecture/hcm_01_characterization_packet.md`
  (PREPARED → COMPLETED).
- `docs/UPCOMING_WORK.md`: P7.9 marked `[x]` (metapackage live on PyPI; the
  phase-7 README already said SHIPPED).

**Phase 2 — deletions (done, 26 files):** `temp_analysis_archive/` (16),
`v2_planning/{v2_roadmap.md, v2_brainstorming_conversation.md, options/}` (5),
`e3_rag_chroma_recovery_capsule.md`, `specs/archive/phase_f_specialized_agents/{handoff_spec.md, schemas.py}`,
`docs/internal/review_prompts/review_prompt_inception_sweep.md`.

**Deviations from §3.1, deliberate (conservative):**
- `v2_planning/v2_architecture_spec.md` **retained** (the one V2 artifact with
  decision-provenance value; §7 open decision).
- `phase_0/05_cycle_a_contract_first.md` **retained**: this plan's own §3.1
  mistakenly claimed zero refs; it is linked from
  `docs/architecture/phase_0/README.md:56`. It will be removed together with the
  `phase_0/` archive move in phase 3, where the README row is repointed.

Net effect: `docs/` loses 26 files of dead material with zero reference breakage;
everything removed is recoverable from git history.

### 2026-10-12 — phases 3–4 (branch `docs/consolidation-phase-3-moves`)

**Phase 3 — grouping + moves (done).**

- **AG track** → `docs/architecture/agent-controls/`: `agent_controls_plan.md`,
  `agent_controls_decision.md`, `ag-03a-protected-publisher-feasibility.md`;
  `archive/`: `ag-01`, `ag-02`, `agent_control_enforcement_map.md`,
  `agent_layer_reassessment_2026-10-12.md`.
- **HCM track** → `docs/architecture/harness-core-modularity/`:
  `harness_core_modularity_roadmap.md`,
  `hcm_05_mcp_recon_adapter_characterization.md`; `archive/`: `hcm_01`,
  `hcm_04e`.
- **WP-01 delivery archive** → `docs/architecture/wp01/`: the E1–E4 packet set,
  `wp01_e3_adoption_status.md`, `e3_residual_repair.md`.
- **ADRs** → `docs/architecture/decisions/`: `td_e3_currentness_decision.md`.
- **Legacy archive** → `docs/internal/architecture/`: `phase_0/`,
  `phase_5/` (blueprint: README/BLUEPRINT/PLAN/COMPONENTS; `SPECS.md` stayed
  live at `docs/architecture/phase_5/`), `phase_6/`, `v1_analysis/`
  (was `v1_specification/`), `v2_planning_spec.md`,
  `tooling-refresh/` (the two zero-ref refresh reports).
- **Four entrypoint READMEs created**: `agent-controls/`, `harness-core-modularity/`,
  `wp01/`, `decisions/`.
- **Link repair**: automated resolver fixed 10 files' relative links and 33
  files' literal path strings; the E2 conformance test's runtime path constant
  (`tests/conformance/test_e2_extraction_boundary.py`) updated to the new
  `architecture/wp01/` location; two legacy-archive depth errors fixed manually.
  Verified: **0 broken links touching moved files** (the 57 remaining broken
  links are pre-existing `specs/deep-audit` cross-refs).

**Phase 4 — indexes (done).** `docs/architecture/README.md` rewritten (Active
work / Governance / lifecycle map / folders / archive) and `docs/README.md`
rewritten (Start here / Current program / System architecture / Reference /
Archive / Specifications).

**Deviations, deliberate:**
- `tools/**` and `workspaces/**` path strings were rewritten by the automated
  pass and then **reverted**: editing `tools/<kit>/` would trip the toolkit
  ownership gate (kit repo + pin + vendored-sync), and workspace files are out
  of scope. The stale doc paths inside kit docstrings/tests are recorded
  follow-up debt for the owning kit repos.
- `UPCOMING_WORK.md` keeps its name (not renamed to `ROADMAP.md`) to avoid a
  link cascade; it is re-pointed from the new index.
- `inception_recon_scientific_review.md` stays in the architecture root: it is
  a live review cited by the AG set, not an archive record.

### 2026-10-12 — archive purge (branch `docs/consolidation-archive-purge`)

Owner authorized deleting the remaining archives and old phases. Removed
**41 files / ~17,400 lines** (all recoverable from git history):

- `docs/internal/architecture/`: `v1_analysis/` (4), `phase_0/` (6),
  `phase_5/` blueprint (4), `phase_6/` (1), `v2_planning_spec.md`,
  `tooling-refresh/` (2).
- `docs/internal/audits/` (3), `docs/internal/review_prompts/` (1).
- `docs/internal/ecosystem/`: `NEXUS_ECOSYSTEM_ANALYSIS.md`,
  `NEXUS_HARNESS_SYNTHESIS.md`, `NEXUS_PHP_ANALYSIS.md`.
- `specs/archive/` (16 — the executed Phase A–F sprint checklists + early draft
  contract).

**Retained exception:** `docs/internal/ecosystem/NEXUS_MASTER_SPECIFICATION.md`
is cited by a kit source comment
(`tools/scholar-search-kit/src/scholar_search/completeness.py`); deleting it
would orphan that comment, which can only be fixed in the kit repo.

**Referrers updated:** `docs/README.md` §5, `docs/architecture/README.md`
(intro + Phase 0/6 rows + historical-archive section), `docs/UPCOMING_WORK.md`
(4 links), `specs/README.md` §4, `specs/exploratory-grounding-agent/README.md`
+ `01_problem_definition.md`, `docs/internal/README.md`.

Result: `docs/internal/` = `README.md`, `COMMIT_SNAPSHOTS.md`, this plan, and one
externally-cited analysis; `specs/` = the normative remediation set + the live
domain series. No historical archive folders remain.

