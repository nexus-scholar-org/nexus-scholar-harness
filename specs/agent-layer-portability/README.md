# Agent Layer Portability

**Status:** DELIVERED — Phases A–E merged (see §10). This document is now the
historical design of record plus the delivery evidence; it no longer authorizes
new implementation by itself.
**Date:** 2026-10-23 (delivery record added 2026-10-29)
**Owner surface:** harness (`.opencode/agent/`, `.agents/skills/`, `src/scholar_harness/`)
**Related:** `docs/architecture/contract_v1_baseline.md`, `specs/deep-audit-remediation-2026-09-17/`, `specs/inception-ecosystem/`

---

## 1. Why this spec exists

The Nexus Scholar agent layer is currently designed for exactly one operator: the person who wrote it, running opencode inside this repository, with full filesystem access and a mental model of what each role is *supposed* to do.

That is a legitimate design target for a development loop. It is not a design target for:

- a second researcher using the harness on their own machine;
- a hosted application where the user never sees a role, a kit, or a pin;
- an auditor asking whether a review was actually produced the way the protocol says it was.

This spec defines the minimum restructuring that makes one agent layer serve all three, without forking into "dev agents" and "product agents."

## 2. What is wrong today (evidence)

Roles are declared as prose personas with a permission map. The prose and the map disagree, and at runtime the map wins:

| File | Prose claim | Machine grant |
|---|---|---|
| `.opencode/agent/screening-critic.md` | "Do not edit the batch, decisions, criteria, protocol, or audit journal; your only write is the assigned critique artifact" | `edit: allow` |
| `.opencode/agent/reviewer.md` | "You are read-only: file edits are denied" | `permission: allow` *(reverted 2026-10-25)* |

The `reviewer.md` row was accurate until 2026-10-25, when the local relaxation was reverted to the committed `edit: deny` / `bash: ask`. It is retained here as the historical trigger for §0 of `05_migration_plan.md`. **All three rows are closed by Phase A**: the committed agent files now match their prose (`edit: deny` for the critic, reviewer and tester), and `tests/conformance/` pins the generated permissions to `roles/*.json`.
| `.opencode/agent/tester.md` | "You are a verifier only. You DO NOT: Write code" | `permission: allow` |

Three further structural facts:

1. **Roles cannot leave opencode.** They are `.md` files loaded by one runtime. An application cannot import them, and no second runtime can be added without reimplementing the role definitions.
2. **Skills are welded to this filesystem.** They instruct `uv run <cli>`, cite repo-relative paths, and (in one case) carry a stale commit SHA in prose. All three fail outside this repo.
3. **Handoffs are untyped.** A role "writes decisions" with the schema living in prose. Failure arrives as a stack trace or a silent omission, not as a value.

A fourth fact is a design omission rather than a defect: **the human is not a role.** Option C requires a lead reviewer to confirm all agent triage, and that confirmation exists only as a sentence in `protocol.json`. The accountability point of the method has no artifact.

## 3. The design claim

> The agents are not the product. The skills are not the product. **The artifact protocol is the product.**

If roles, skills, and runtimes are all replaceable without touching the protocol, then "make this usable by others" becomes packaging rather than rewriting.

## 4. The four layers

| Layer | Answers | Changes when | Consumed by | Never contains |
|---|---|---|---|---|
| **Role** (`roles/*.json`) | Who may do what, to which paths, producing which schema | science or policy changes | the runner / adapter | prose about behavior, commands |
| **Skill** (`.agents/skills/*/SKILL.md`) | How to do it well | tooling improves | the agent prompt | versions, absolute paths, pins |
| **Envelope** (`Envelope@1`) | What crosses a boundary | the data contract changes | the validator | narrative, unstructured fields |
| **Capability** (`CapabilityAdapter`) | Where it runs | deployment changes | the app / dev loop | science, policy |

Today all four are fused inside twelve markdown files. That is why changing one thing changes four.

## 5. Non-goals

- **Not a general agent framework.** No competing with orchestration libraries. The advantage is the protocol, the blinding, and the lineage.
- **Not an LLM runtime decision.** This spec does not require the harness to host a model. Roles are descriptions of capability; the adapter decides what executes them. Model selection, cost, and prompt strategy stay out of scope.
- **Not a rewrite of the fourteen skills.** They are the highest-quality asset in the repo. They need a resolver preamble and pin hygiene, not new content. (`pull-request-gate` is dev-only and is excluded from app packaging; the other thirteen are research-facing.)
- **Not a change to `Contract v1`.** Role and envelope changes do not modify `docs/architecture/contract_v1_baseline.md` artifacts. Any overlap requires a separate architecture decision.
- **Not authorization to edit agents.** Phase A changes real permission files. It is gated on the baseline being green first (see §7).

## 6. Index

| File | Contents |
|---|---|
| [`01_role_model.md`](01_role_model.md) | Role schema, field semantics, catalogue of all 12 roles (Phase C adds `human-confirm`), permission codegen, drift test |
| [`02_envelope_and_refusals.md`](02_envelope_and_refusals.md) | Envelope schema, status algebra, refusal-code registry, hashing and parent binding |
| [`03_skills_portability.md`](03_skills_portability.md) | Skill frontmatter, environment preamble, portability test, pin hygiene |
| [`04_capability_adapter_and_app_surface.md`](04_capability_adapter_and_app_surface.md) | Adapter interface, structural independence, `HumanConfirmation@1`, what end users see |
| [`05_migration_plan.md`](05_migration_plan.md) | Phases, acceptance criteria, negative tests, validation commands, risks |

## 7. Preconditions

Phase A edits permission files and therefore cannot start from a drifted baseline:

```
uv run python scripts/generate_contract_baseline.py --check
```

As of 2026-10-25 this exits **0** — the drift caused by the local `.opencode/agent/reviewer.md` relaxation was resolved by reverting that file (see `docs/architecture/decision_t_sc1_acceptance_without_review_2026-10-23.md` §8). Any Phase-A packet that starts with a red baseline returns `BLOCKED_BASELINE_DRIFT`.

## 8. Phase summary

| Phase | Deliverable | Kills | Effort |
|---|---|---|---|
| A | `roles/*.json` + generated permissions + drift test | The three prose/config contradictions; duplicate `opencode.json` declarations | ~1 day |
| B | `Envelope@1` + status algebra | Untyped handoffs; stack-trace failures | ~0.5 day |
| C | `HumanConfirmation@1` | The missing accountability artifact | ~1 day |
| D | Skill environment preamble + portability test | `uv run` and repo-relative paths in skills | ~1 day |
| E | `CapabilityAdapter` with two implementations | The coupling of scientific roles to opencode | ~2 days |

Ordering is by leverage per unit of effort, not by dependency alone. A, B, and C are independent of each other and can be parallelised across agents; D depends on B; E depends on A, B, and D.

## 9. Definition of done for the whole spec

A stranger can be handed a workspace and a protocol and complete a review without reading any file under `.opencode/agent/`, and an auditor can verify that every artifact was produced by the role that claims to have produced it — with a refusal reason for every absent row.

## 10. Delivery record (2026-10-29)

All five phases merged on `nexus-scholar-org/nexus-scholar-harness`. The
phase documents above remain the design of record; this table is the evidence
that the design is implemented.

| Phase | Deliverable | Merged evidence |
|---|---|---|
| A | `roles/*.json`, generated permissions, drift test | PR #149 |
| B | `Envelope@1` + refusal registry | PR #150 |
| C | `HumanConfirmation@1` validator, signing producer, export gate, `roles/human-confirm.json` | PR #151; closure PR #156 (`86e49eb`) |
| D | Skill portability: placeholder registry, per-skill wheel bundle, `SKILL.meta.json` | PR #152 |
| E | `CapabilityAdapter` with `OpencodeAdapter` + `InProcessAdapter` | PR #153/#154; Python 3.11/3.12 run-view repair PR #155; residual-limits record PR #159 |

Two bounded follow-ups merged with Phase E: the access-denied lock path is now
typed contention rather than a crash on Windows (PR #158), and the app-mode
accepted limits A1–A7 are recorded in
`docs/architecture/agent_capability_adapters.md`.

Remaining limits are **accepted behaviour, not undelivered phases**: dev mode is
best-effort, app-mode handlers are trusted code, and egress/redaction/promotion
scope is recorded in that residual-limits section. Widening any claim requires
an enforcement change (OS sandbox, subprocess boundary, transactional
publisher), not another documentation pass.
