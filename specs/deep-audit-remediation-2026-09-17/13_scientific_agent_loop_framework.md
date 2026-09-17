# Scientific Agent Loop Composition Framework

**Version:** 0.1.0-proposal  
**Status:** Draft — not yet an execution contract  
**Purpose:** Compose Nexus Scholar kits into bounded, auditable scientific tasks

## 1. Motivation

The kits expose useful capabilities, but a scientifically defensible workflow is
not merely a sequence of tool calls. It is a controlled loop with:

- one explicit scientific question or decision;
- frozen inputs and method assumptions;
- observable intermediate artifacts;
- a critique or verification step;
- a bounded iteration policy;
- human authority at consequential gates;
- a stop condition that does not equate exhaustion with truth;
- claim language limited by the evidence actually produced.

This framework defines how proposed agent loops should be specified. The catalog
in `14_scientific_agent_loop_catalog.md` applies it to concrete research tasks.

## 2. Design principles

### LOOP-PR-001 — One active scientific objective

Each loop MUST optimize one named scientific objective. A loop may produce
supporting artifacts, but it MUST NOT quietly expand from, for example, query
recall analysis into manuscript novelty claims.

### LOOP-PR-002 — Kits remain capability owners

The coordinating agent MUST call toolkit APIs/CLIs/MCP tools rather than
reimplementing search, protocol validation, PDF verification, graph analysis,
RAG retrieval, or Phase-4 trust rules.

### LOOP-PR-003 — Artifact-mediated state

Durable state MUST live in versioned workspace artifacts. Chat history and agent
memory are not canonical state.

### LOOP-PR-004 — Critic separation

When an agent proposes a scientific decision, a critic step MUST evaluate it
against frozen criteria and source artifacts. The critic MAY be the same model in
a separately prompted role, but its inputs, rubric, and output must be recorded.

### LOOP-PR-005 — Negative results persist

Failed searches, inaccessible PDFs, excluded studies, contradictions, null
effects, failed transfer, unresolved claims, and verification failures MUST be
retained. They are not disposable debugging output.

### LOOP-PR-006 — Human authority

Agents may prepare, recommend, rank, or flag. Humans retain authority for:

- protocol freeze and material amendments;
- final inclusion/exclusion where the review method requires human screening;
- adjudication of scientifically consequential conflicts;
- acceptance of risk-of-bias judgments not fully deterministic;
- approval of manuscript-level novelty and causal claims;
- exceptions that weaken a predefined rigor gate.

### LOOP-PR-007 — Bounded adaptation

Every adaptive loop MUST define maximum iterations, marginal-gain measurement,
and a non-success terminal state. “Continue until satisfied” is forbidden.

### LOOP-PR-008 — Method provenance

Every decision records whether it came from `HUMAN`, `DETERMINISTIC_RULE`,
`HEURISTIC`, `LLM`, `EXTERNAL_PROVIDER`, or a composed method. Silent fallback
between methods is forbidden.

## 3. Canonical loop specification

Every executable or proposed loop should use this shape:

```yaml
loop_id: LOOP-<domain>-<number>
version: 0.1.0
name: Human-readable task name
status: PROPOSED
scientific_objective: One falsifiable or decision-oriented objective
entry_conditions:
  - Required artifact and state
inputs:
  - artifact_type: protocol
    path: protocol.json
    fingerprint: required
roles:
  coordinator: orchestration agent
  workers: [specialist agents]
  critic: independent rubric role
  human_gate_owner: named role
capabilities:
  - kit: scholar-search-kit
    operation: search
    surface: python|cli|mcp
states: [READY, RUNNING, REVIEW, ...]
iteration:
  maximum_rounds: 3
  progress_metric: explicit metric
  minimum_gain: explicit threshold
artifacts:
  - produced path/schema
decision_points:
  - condition, options, authority
stop_conditions:
  success: [...]
  bounded_inconclusive: [...]
  failed: [...]
claim_boundary:
  allowed: [...]
  prohibited: [...]
audit_events: [...]
```

## 4. Common loop state machine

```text
PROPOSED
   │ design approved
   ▼
READY ── invalid/missing input ──► BLOCKED_INPUT
   │
   ▼
RUNNING ── partial failure ──────► DEGRADED_REVIEW
   │                                  │
   ▼                                  │ accepted with limits
CRITIC_REVIEW ◄───────────────────────┘
   │
   ├─ material scientific choice ───► HUMAN_DECISION
   │                                    │
   │                                    ├─ revise ─► READY (new iteration)
   │                                    └─ accept
   ▼
COMMIT_ARTIFACTS
   │
   ├─ criteria met ─────────────────► COMPLETE
   ├─ bound reached/no gain ────────► INCONCLUSIVE
   └─ integrity failure ────────────► FAILED
```

`BLOCKED_INPUT`, `INCONCLUSIVE`, and `FAILED` are valid scientific outcomes and
must not be coerced to `COMPLETE`.

## 5. Roles

### 5.1 Coordinator

- loads the loop spec and frozen inputs;
- dispatches bounded worker tasks;
- checks artifact schemas/fingerprints;
- enforces iteration and stop conditions;
- never makes an unlogged protocol amendment;
- commits artifacts only after critic/human gates.

### 5.2 Specialist worker

- owns a narrow kit-backed subtask;
- returns structured outcome plus artifact references;
- reports partial failures and limitations;
- does not broaden the scientific objective.

### 5.3 Critic

- evaluates against a stored rubric;
- actively checks identity, missingness, negative evidence, leakage, unfair
  comparisons, unsupported causality, and alternative explanations;
- emits `APPROVE`, `REVISE`, `ESCALATE`, or `INCONCLUSIVE` with reasons;
- cannot modify canonical artifacts directly.

### 5.4 Human gate owner

- receives the smallest decision packet needed;
- sees alternatives, evidence, disagreements, and consequences;
- records choice and rationale;
- may not retroactively alter earlier frozen artifacts without an amendment run.

## 6. Artifact model

Each loop run stores:

```text
<workspace>/loops/<loop-id>/<run-id>/
  loop_spec.json
  run_manifest.json
  inputs.json
  worker_results/
  critic_report.json
  decision_packet.md
  human_decision.json        # when applicable
  outputs.json
  limitations.md
```

The run manifest MUST reference, not duplicate, canonical workspace artifacts.
Large generated artifacts remain in their domain directories; the loop records
their paths, hashes, schemas, and producer versions.

## 7. Iteration policy

An adaptive loop declares:

1. maximum rounds;
2. budget per round;
3. mutable variables;
4. frozen variables;
5. progress metric;
6. minimum meaningful gain;
7. regression checks;
8. termination reason vocabulary.

Example for discovery expansion:

- mutable: query synonyms, one citation-snowball frontier;
- frozen: RQs, inclusion/exclusion criteria, date/language bounds;
- maximum rounds: three;
- progress: new eligible unique studies plus golden-seed recall;
- stop: zero new eligible studies in two rounds or bound reached;
- prohibited: changing criteria to admit newly found attractive evidence without
  a protocol amendment.

## 8. Scientific decision packet

Every human gate should receive:

- decision to make;
- frozen question and criteria;
- options considered;
- supporting and contradicting evidence;
- missingness/provider failures;
- critic recommendation and confidence basis;
- impact on downstream artifacts;
- exact claim language enabled by each option;
- proposed next action and cost.

## 9. Claim boundary model

Loops declare allowed and prohibited conclusions. Baseline vocabulary:

| Evidence state | Allowed phrasing | Prohibited phrasing |
|---|---|---|
| Search completed with provider failures | “The successful providers returned…” | “No literature exists” |
| No legal OA PDF resolved | “No legal OA full text was resolved by configured sources” | “The paper is paywalled” |
| Embedding similarity high | “Semantically related/supportive passage” | “Claim entailed/verified” |
| One benchmark/fold | “Observed on this benchmark/fold” | “Generally superior” |
| Retraction metadata unresolved | “Retraction status unresolved” | “Not retracted” |
| Null/negative transfer | “Did not transfer under tested conditions” | omission from final synthesis |

## 10. Safety and failure rules

- No loop may index an extraction marked failed or stub-only.
- No loop may count a corpus/workspace ID as a unique study.
- No loop may advance through screening on an unmatched fingerprint.
- No loop may treat LLM fallback as the originally requested method.
- No loop may overwrite a frozen protocol; amendments create a new fingerprint
  and invalidate dependent results.
- No loop may mark a claim trusted merely because no Phase-4 flag was found.
- No loop may use live-log observations as paper-facing results without persisted
  artifacts and parsed summaries.

## 11. Scheduling and concurrency

Parallel workers are permitted only when:

- they operate on disjoint items or immutable inputs;
- result ordering is normalized deterministically;
- concurrency limits respect provider contracts;
- each item retains independent outcome/provenance;
- aggregation waits for all required workers or explicitly records missing work.

Parallelism is inappropriate for sequential adaptive choices where one round's
evidence changes the next round's query or rubric.

## 12. Loop-level quality metrics

Metrics are task-specific, but every loop reports:

- input and output coverage;
- failed/partial/unresolved counts;
- method provenance distribution;
- critic disposition counts;
- human overrides and reasons;
- iterations and marginal gain;
- identity/provenance validation status;
- artifact/schema validation status;
- claim-boundary violations detected.

Metrics describe process evidence; they do not automatically certify scientific
quality.

## 13. Loop registration and execution

Proposed registry fields:

- `loop_id`, version, title, scientific phase;
- compatible protocol playbooks;
- required/optional capabilities;
- entry and exit artifact schemas;
- human gates;
- default iteration limits;
- estimated network/compute cost class;
- offline capability;
- risk classification;
- implementation status.

An unimplemented proposal may appear in planning/UI surfaces, but the runtime must
reject execution with `UNSUPPORTED_LOOP`, not approximate it with unrelated tools.

## 14. Verification requirements

Before a loop becomes executable:

1. validate its schema;
2. run happy, partial, inconclusive, failed, and human-revision fixtures;
3. demonstrate iteration bound enforcement;
4. demonstrate exact artifact/audit lineage;
5. test every claimed surface and capability;
6. conduct a hostile-reviewer evaluation of permitted/prohibited claims;
7. document expected human workload and any model/provider dependency.

## 15. Definition of done for the framework

- Loop schema and state vocabulary are approved.
- Cross-kit contracts in `10_cross_kit_contracts.md` are reused rather than
  duplicated inconsistently.
- At least one loop in each scientific phase has a golden execution fixture.
- Human gate packets are user-tested.
- Runtime refuses unsupported or schema-incompatible loops safely.
- Loop outcomes and scientific claims remain distinguishable.

### Registry note (2026-09-17 remediation)

The `LOOP-*`/`SCI-LOOP-*` identifiers and the `<workspace>/loops/<loop-id>/<run-id>/`
artifact tree proposed here are **not yet entries in the canonical identifier
registry or artifact registry** of `10_cross_kit_contracts.md` (XC-001, XC-006).
This document may propose them, but they become normative only after a contract
revision registers them. Loop run-state vocabulary (`SUCCESS`, `PARTIAL`,
`FAILED`, `SKIPPED`, `WAITING_FOR_DECISION`, `CANCELLED`) SHALL use the shared
outcome status set of `10_cross_kit_contracts.md` §5 (XC-011–XC-014), including
the `ERROR`/`FAILED` alias rule (XC-012a), and this document is tagged a
proposal pending that registration.

