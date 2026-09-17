# Dependency-Ordered Execution Roadmap

**Version:** 1.0.0-draft  
**Status:** Proposed delivery sequence  
**Planning principle:** Contract foundations before feature repair

## 1. Delivery strategy

This remediation must not be implemented as nine isolated cleanup efforts. The
highest-risk defects share identity, artifact, outcome, and provenance contracts.
The work is therefore arranged in waves that establish contracts before adapting
producers and consumers.

Each toolkit change belongs in its canonical repository. The harness receives
vendored snapshots and pin updates only after the toolkit PR lands. Use one
branch/PR per repository and follow the fork contribution gate.

## 2. Work-package overview

| WP | Title | Priority | Primary owner | Depends on | Effort (person-days) |
|---|---|---:|---|---|---:|
| WP-00 | Freeze decisions and schemas | P0 | Architecture/harness | — | 3–5 |
| WP-01 | Canonical identity and artifact envelopes | P0 | Protocol + search + harness | WP-00 | 8–12 |
| WP-02 | RAG evidence identity and non-fabrication | P0 | RAG | WP-01 | 8–12 |
| WP-03 | Screening generation gate | P0 | Harness + search contracts | WP-01 | 6–10 |
| WP-04 | Typed executable PipelineSpec | P0 | Harness/console | WP-00 | 10–15 |
| WP-05 | Agent pipeline truthfulness and validation | P0 | Agent + harness | WP-04 | 6–10 |
| WP-06 | Transitive dedup and conservative resolution | P1 | Search + bib | WP-01 | 6–10 |
| WP-07 | PDF validation and extraction truthfulness | P1 | PDF | WP-01 | 6–10 |
| WP-08 | Graph mode correctness and graph contract | P0/P1 | Graph + RAG | WP-01 | 5–8 |
| WP-09 | Protocol compile/validation integrity | P0 | Protocol | WP-00 | 6–10 |
| WP-10 | Phase-4 trust and open-science integrity | P1 | Verify | WP-01, WP-02 | 8–12 |
| WP-11 | Unified outcomes, audit, and lifecycle | P1 | All + harness | WP-01 | 10–15 |
| WP-12 | Packaging and surface parity | P1/P2 | All kit owners | Relevant kit fixes | 8–12 |
| WP-13 | Legacy migrations | P1/P2 | Harness + kit owners | WP-01–12 | 8–14 |
| WP-14 | Documentation regeneration and release | P2 | Docs/release | WP-01–13 | 6–10 |

Effort figures are planning ranges for one experienced contributor per work
package, excluding review latency and CI queue time. Cross-repository
coordination (each kit change is its own repo/PR under the contribution gate)
can add 30–50% to wall-clock time without changing the person-day estimate.
The critical path is `WP-00 → WP-01 → {WP-02 → WP-10, WP-11} → WP-12 → WP-13 → WP-14`.

Documents `13_scientific_agent_loop_framework.md` and
`14_scientific_agent_loop_catalog.md` are design proposals. No work package in
this roadmap sequences them, and they impose no delivery obligation until a
future roadmap revision assigns a work package, gate, test owner, and registered
identifier prefixes (see the registry notes in those documents).

## 3. Wave 0 — Decisions and executable schemas

### WP-00 deliverables

1. Approve the canonical distinction:
   `workspace_id`/corpus, `study_id`/paper, `document_id`/full text,
   `chunk_id`/evidence unit, `claim_id`, and `evidence_id`.
   (Canonical semantics are published in `10_cross_kit_contracts.md` §3
   XC-001a; WP-00 approves and binds them.)
2. Approve artifact envelope v1 and operation outcome v1.
3. Approve DOI normalization while keeping provider IDs external.
4. Approve claim-verification vocabulary: semantic support, verbatim match,
   entailment, and trust context as independent axes.
5. Approve correction/addendum severity policy.
6. Approve PipelineSpec v1 typed argument model and custom-command policy.
7. Publish JSON Schemas and golden fixtures under a stable shared location.
8. Approve strict versus best-effort discovery mode defaults and their
   representation in the search batch outcome (`00_system_scope_and_findings.md`
   §8 decision 3; operationalized in `02_search_kit_spec.md` requirements 3–4).
9. Approve the backward-compatibility window for existing unversioned
   workspaces and legacy screening artifacts, including whether re-screening is
   mandatory (`00_system_scope_and_findings.md` §8 decision 7;
   `01_harness_spec.md` §7 migration rules).
10. **Test-infrastructure prerequisite (before any Wave 1 test work):** remove the
    repository-wide fixed `--basetemp=tests_temp` configuration and give every
    suite a unique temporary root (`11_validation_and_test_plan.md` VAL-TMP-001/
    VAL-TMP-002; `01_harness_spec.md` HAR-T019). This is deliberately promoted
    from WP-12 into Wave 0: parallel Wave 1–3 test runs would otherwise reproduce
    the same collision that caused the audit's setup error. The WP-12 line item
    is retained only as a verification that it stays fixed.
11. **Time-box:** WP-00 decisions MUST be frozen within **5 working days** of
    program start. If a decision is unresolved at the deadline, the named
    architecture owner records the conservative default (existing behavior for
    discovery/back-compat; no new ID semantics) and the decision moves to an
    explicit ADR-backed follow-up with an owner and expiry. Downstream WPs MUST
    NOT begin on an unresolved identifier/envelope decision.

### Residual status vs. Phase A–F work

Phase A–F commits in this repository closed many *adjacent* defects, and several
audit findings are partial residuals rather than untouched code. Live source was
re-verified on 2026-09-17; the following MUST be treated as still-open unless a
dated regression test proves otherwise:

| Finding | Phase A–F status | Current evidence |
|---|---|---|
| SYS-009 graph coupling/hybrid | **Not fixed** — still broken | `cli.py:131` passes `min_jaccard` to `build_bibliographic_coupling`, whose API takes `min_overlap` (`scientometrics.py:189`); `cli.py:139` passes `alpha` to `build_hybrid_network`, whose API takes `weight_cocite`/`weight_couple` (`:245`). Both raise `TypeError`. Co-citation at `cli.py:123` is correctly called and is not part of this defect |
| SYS-013 MCP file-path protocol validation | **Not fixed** — still broken | `tools/scholar-agent-kit/src/scholar_agent/server.py:232-235` still calls `model_validate` on raw file text; `tests/test_server.py:68-71` still fails |
| SYS-006 `golden_seeds` | **Partial residual** | Field exists in `scholar_protocol.models.SearchStrategy` (added Phase B) but `IntentPacket`/`compiler.py` still drop it; the model-level fix did not carry through the intent path |
| SYS-005 MCP `query`/`skip_stages` | **Not fixed** | `nexus_pipeline_run` still ignores `query` and filters stages after execution |
| SYS-001 `scholar-search run` template | **Not fixed** | All five built-ins still use the nonexistent subcommand |

Implementation owners MUST re-verify each finding against the live tree before
claiming it is already resolved by Phase A–F; the traceability ledger's `status`
column is the single source of truth.

### Gate G0

- Decisions recorded in ADRs or equivalent.
- Golden fixtures validate.
- Consumer owners sign off on migration approach.
- No runtime code merges ahead of unresolved identifier semantics.
- WP-00 decisions frozen within the 5-working-day time-box (or a documented
  conservative default plus owner/expiry is recorded).
- Parallel-safe test temporary roots are in place and proven by running the
  Wave 0 suite with at least two concurrent workers (VAL-TMP-001/HAR-T019).

## 4. Wave 1 — Stop scientifically unsafe behavior

Wave 1 items may run in parallel after G0.

### WP-02 — RAG identity and evidence honesty

- Introduce per-paper study identity in indexing and retrieval metadata.
- Change citation tokens, synthesis claims, matrices, and consensus to use it.
- Replace invented matrix defaults with `NOT_REPORTED`/null plus provenance.
- Rename embedding “entailment verification” or implement a genuine supported
  entailment path; never emit unqualified `VERIFIED`.
- Add two-paper and negative-claim regression corpora.

### WP-03 — Screening generation gate

- Fingerprint protocol, verified corpus, batches, decisions, and collected output.
- Reject stale/mixed decision generations.
- Make orchestrator resume conditional on matching screening run.
- Archive legacy/old generations recoverably.

### WP-04 — Executable PipelineSpec

- Add typed argument kinds and migrate built-ins.
- Replace `scholar-search run` and invalid positional/boolean rendering.
- Add CLI registry validation.
- Fix unknown-edge crash and deterministic topological order.

### WP-05 — Agent tool truthfulness

- Fix file-path protocol validation.
- Implement actual query override/skip-stage behavior or reject parameters.
- Surface LLM-to-heuristic fallback as partial with method provenance.
- Bind recon root after workspace option resolution.

### WP-08 — Graph broken modes

- Repair coupling/hybrid signature parity immediately.
- Preserve nodes and metadata across transforms.
- Resolve Louvain-versus-greedy naming and seed behavior.

### WP-09 — Protocol integrity

- Run full cross-field validation during compile.
- Preserve golden seeds through intent/compiler.
- Correct extraction types.
- Reject unknown fields at authoring boundaries.

### Gate G1

- No known P0 execution or scientific-integrity defect remains.
- Two-paper end-to-end identity scenario passes.
- Built-in pipelines parse and execute hermetically.
- Stale screening cannot unlock downstream work.
- MCP parameters have truthful semantics.

## 5. Wave 2 — Reliability and failure visibility

### WP-06 — Search and bibliography identity merging

- Implement connected-component/union-find identity merging.
- Preserve stable canonical ID and alias/lineage map.
- Add conservative Crossref resolution with thresholds and ambiguity state.
- Make JSON/Bib round-trips lossless for declared fields.
- Bound concurrency and close clients.

### WP-07 — PDF acquisition and extraction

- Apply strict validation to downloads and cache hits.
- Use staged bounded downloads and atomic replace.
- Define structured extraction success/partial/failure.
- Standardize metadata for Markdown engines.
- Separate institutional gateway rewriting from forward proxy transport.

### WP-10 — Verification integrity

- Count any Phase-4 evidence when assessing coverage.
- Ensure retraction-only evidence blocks trust.
- Correct negation precedence and link locality/type association.
- Align correction severity with approved policy.
- Align CLI and MCP stream selection and dry-run semantics.

### WP-11 — Outcomes, audit, and lifecycle

- Adopt structured outcome envelopes on Python/JSON CLI/MCP surfaces.
- Consolidate harness audit writer and stable event IDs.
- Add node-run manifests and fingerprint-based idempotency.
- Close clients and make cancellation/partial outcomes explicit.
- Make multi-file publication atomic through run manifests.

### Gate G2

- Provider/LLM/network failures cannot look like valid empty success.
- Interrupted writes leave no partial canonical artifact.
- Transitive dedup cases pass in search and bib.
- Strict PDF and Phase-4 negative controls pass.
- Audit/state agree with real outcomes.

## 6. Wave 3 — Packaging, parity, and migration

### WP-12 — Packaging and parity

- Declare direct runtime imports in every package.
- Remove unused dependencies or justify them.
- Build/install every wheel in an isolated environment.
- Run exact configured entrypoints and enumerate MCP tools.
- Generate/check capability registry and CLI/API/MCP parity fixtures.
- Verify the Wave 0 parallel-safe temporary-root configuration remains fixed
  (VAL-TMP-001/VAL-TMP-002; implementation moved to WP-00 deliverable 10).

### WP-13 — Legacy migration

- Detect unversioned artifact sets and legacy PipelineSpecs.
- Provide dry-run migration reports.
- Back up before mutation.
- Migrate identifiers without losing original aliases.
- Mark artifacts whose provenance cannot be reconstructed
  `LEGACY_UNVERIFIED`; do not invent lineage.
- Require re-screening where fingerprints cannot be established.

Concrete example — an unversioned artifact set is any workspace produced before
this remediation, e.g.:

```text
workspaces/<slug>/
  protocol.json                     # no schema_version, no fingerprint
  literature/
    candidates.json                 # records keyed by SCI-* only
    included.json                   # bare JSON array of documents
  literature/screening/
    batch_000.json  batch_000_decisions.json   # no screening_run_id, no schema_version
  extracted/<paper>.md              # frontmatter with workspace_id only, no study_id
```

Migration behavior for this example:

1. `migrate --dry-run` reports, per artifact: detected schema (legacy v0),
   reconstructable fields, and unreconstructable fields.
2. `protocol.json` is recompiled from its raw fields; because no compiler/intent
   provenance exists, the compiled protocol is written with
   `provenance: {status: "LEGACY_UNVERIFIED", reason: "no_compiler_provenance"}`.
3. `candidates.json` records keep their `SCI-*` IDs as `study_id` aliases; a
   `study_id` is derived deterministically (XC-005) and the original ID is
   preserved in the alias map (XC-003).
4. Screening batches/decisions lack `screening_run_id`; they are archived to
   `literature/screening/legacy/<timestamp>/` and the workspace is marked as
   requiring re-screening (`screening_generation: LEGACY_UNVERIFIED`). An old
   `included.json` MUST NOT unlock downstream stages (HAR-SCR-005).
5. `extracted/*.md` missing `study_id` are re-derived from DOI/filename where
   possible; otherwise `content_status` stays explicit and the artifact is
   tagged `LEGACY_UNVERIFIED`. No `study_id` is fabricated.
6. Every migrated artifact is written atomically, its pre-migration copy is
   retained under `migration_backup/<timestamp>/`, and the operation is
   idempotent: a second run is a no-op.

A `LEGACY_UNVERIFIED` status MUST remain visible in `status`/`doctor` output
(`01_harness_spec.md` §7 rule 6) and MUST NOT be upgraded to verified merely
because a migration command exited zero.

### Gate G3

- Minimal-install smoke passes for all packages.
- Migration is idempotent and rollback-tested.
- Current and migrated fixtures pass the same consumer contracts.
- Shared editable environment is no longer required to hide missing dependencies.

## 7. Wave 4 — Documentation and stable release

### WP-14 deliverables

- Regenerate `docs/kits_surface_matrix.md` from the live capability registry.
- Synchronize `.agents/skills` and the bundled plugin skills.
- Rewrite stale READMEs/tutorials/API references.
- Publish artifact schemas, outcome/error codes, migration guide, and audit schema.
- Update architecture diagrams to show corpus/study/document/chunk/claim identity.
- Record known limitations and non-claims.
- Update release notes and plugin pins.

### Gate G4

- Documentation commands execute in CI examples.
- Tool counts and signatures match the registry.
- All canonical kit repositories, vendored trees, and full-SHA pins match.
- Full platform suite, contract suite, E2E suite, and release smokes pass.
- P0 count is zero; P1 count is zero or explicitly waived with expiry/owner.

### Gate failure handling, rollback, and escalation

Every gate shares one failure protocol:

1. **Rollback unit.** Each wave is developed on `dev/phase-<wave>` branches and
   integrated into `staging/remediation` behind a tagged checkpoint. A failed
   gate reverts the wave to the last green tag; independently mergeable kit PRs
   may remain landed but MUST be reverted or feature-flagged if they weaken a
   gate. No gate failure is resolved by editing the gate.
2. **Escalation path.** Blocking owner → WP orchestrator → architecture owner →
   repository maintainer. The escalation target for each WP is named in the
   traceability ledger (12 §10 "reviewer sign-off" plus an escalation owner).
3. **Dwell limit.** No gate may remain blocked more than **10 working days**.
   At the limit, the architecture owner must either (a) record an ADR that
   narrows scope with a dated follow-up, or (b) issue a time-boxed waiver.
4. **Waivers.** A P1 MAY be waived only with a named owner, a documented interim
   control, and an expiry date (mirrors Gate G4). A P0 MUST NOT be waived for a
   release claim; it may only be narrowed in scope by ADR. An expired waiver
   automatically re-opens the finding.
5. **Observability.** Gate outcomes, rollback tag, blockers, waiver owner, and
   expiry are recorded in the traceability ledger; the ledger is the single
   source of truth for progress (`12 §10`).

## 8. Repository/PR decomposition

Recommended minimum PR sequence:

| Repository | PR slices |
|---|---|
| `scholar-protocol-kit` | compile validation + golden seeds; extraction typing/strict models |
| `scholar-search-kit` | artifact/identity schema; transitive dedup; outcomes/retry/lossless import |
| `scholar-pdf-kit` | strict download/atomicity; extraction contract; proxy separation |
| `scholar-bib-kit` | connected dedup; resolver safety/lifecycle; atomic CLI writes/docs |
| `scholar-rag-kit` | study identity/non-fabrication; reindex replacement; claim vocabulary/audit |
| `scholar-graph-kit` | broken modes/metadata; failure outcomes; dependencies/docs |
| `scholar-verify-kit` | trust/retraction; open-science classifier; parity/audit contract |
| `scholar-agent-kit` | protocol/pipeline fixes; structured MCP outcomes; recon/dependencies |
| Harness | schemas/fixtures; screening gate; PipelineSpec; audit/state; pins/migrations |

Do not combine unrelated canonical toolkit changes into a harness-only commit.

## 9. Dependency graph

```text
WP-00 Decisions and schemas
 ├─ WP-01 Identity/artifact foundation
 │   ├─ WP-02 RAG identity
 │   ├─ WP-03 Screening gate
 │   ├─ WP-06 Search/Bib dedup
 │   ├─ WP-07 PDF contracts
 │   ├─ WP-08 Graph contracts ──► WP-02 graph-boost parity
 │   ├─ WP-10 Verify integrity ◄─ WP-02 claim identity
 │   └─ WP-11 Outcomes/audit
 ├─ WP-04 PipelineSpec ──► WP-05 Agent pipeline semantics
 └─ WP-09 Protocol integrity ──► WP-03 / WP-06

WP-02..11 ──► WP-12 Packaging/parity ──► WP-13 Migration
WP-12 + WP-13 ──► WP-14 Documentation/release
```

## 10. Progress tracking

Maintain a traceability ledger with one row per normative requirement:

- requirement ID;
- owning repository and work package;
- status: `OPEN`, `DESIGN_APPROVED`, `IMPLEMENTED`, `VERIFIED`, `DEFERRED`;
- PR/commit and pin;
- tests and fixtures;
- migration impact;
- documentation status;
- reviewer sign-off.

Progress percentages must be derived from verified requirements, not file count,
commit count, or passing legacy tests.

### Finding → requirement crosswalk

Every system finding from `00_system_scope_and_findings.md` §5 maps to at least one
normative requirement. The ledger MUST carry this mapping so a finding cannot be
closed while only part of its requirement set is verified.

| Finding | Owning requirements | Owning WPs |
|---|---|---|
| SYS-001 | HAR-CMD-001, HAR-CMD-003 | WP-04 |
| SYS-002 | HAR-SCR-001, HAR-SCR-005, XC-036–XC-040 | WP-03 |
| SYS-003 | XC-001a, HAR-ORC-002, RAG-001–RAG-003, RAG-007 | WP-01, WP-02 |
| SYS-004 | RAG-016 | WP-02 |
| SYS-005 | AG-021, AG-022 | WP-05 |
| SYS-006 | PR-017 | WP-09 |
| SYS-007 | SE-002, BIB-017, BIB-018 | WP-06 |
| SYS-008 | PDF-005 | WP-07 |
| SYS-009 | GR-001 | WP-08 |
| SYS-010 | VR-023 | WP-10 |
| SYS-011 | SE-003, SE-004, XC-013, XC-014 | WP-06, WP-11 |
| SYS-012 | PDF-008 | WP-07 |
| SYS-013 | PR-020, AG-023 | WP-05, WP-09 |
| SYS-014 | GR-002, GR-003 | WP-08 |
| SYS-015 | VR-024, VR-025 | WP-10 |
| SYS-016 | XC-035, XC-047, RAG-019, GR-014, PDF-012, AG-001, AG-002 | WP-12 |
| SYS-017 | HAR-AUD-001–HAR-AUD-007, XC-016–XC-020 | WP-11 |
| SYS-018 | WP-14; each kit spec "Documentation updates" | WP-14 |
| SYS-019 | HAR-CMD-002, HAR-CMD-004, HAR-CMD-005, HAR-CMD-006 | WP-04 |
| SYS-020 | HAR-DAG-001 | WP-04 |
| SYS-021 | HAR-ORC-001, XC-024, SE-011 | WP-11 |
| SYS-022 | VR-001 | WP-10 |

## 11. Stop/go criteria

Stop a wave when:

- a shared schema is being implemented differently by two owners;
- a migration would discard provenance;
- a “fix” converts an explicit failure to an empty success;
- a toolkit change exists only in the vendored tree;
- a P0 test fails;
- the isolated package cannot start without the shared venv.

Proceed to the next wave only after the corresponding gate has durable test and
commit evidence.

## 12. Completion definition

The remediation program is complete when all gates G0–G4 pass, the traceability
ledger covers every MUST requirement, all repository pins are synchronized, and
the system can demonstrate—using hermetic fixtures—that each claim remains tied
to the correct study and evidence while failures remain explicit.

