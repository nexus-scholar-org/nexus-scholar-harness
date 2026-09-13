# Inception Ecosystem — Specification

> **Status:** Live · canonical home for the orchestration skills that compose the
> Nexus Scholar inception flow.
> **Relates:** `specs/exploratory-grounding-agent/` (the grounded recon subsystem this
> ecosystem drives), `.agents/skills/` (canonical skill tree), `.agents/plugins/nexus-scholar/skills/`
> (distribution bundle mirror), `.opencode/agent/inception-agent.md`.

---

## What this folder is

The Nexus Scholar inception phase is orchestrated by **three interdependent
skills** whose boundaries and handoffs were previously only implicit inside the
SKILL.md bodies:

| Skill | Canonical location | Role |
| :-- | :-- | :-- |
| `workspace-manager` | `.agents/skills/workspace-manager/SKILL.md` | **State layer** — scaffold `workspaces/<slug>/`, append-only `audit/journal.jsonl`, `INDEX.md` sync, canonical tool paths. |
| `methodology-copilot` | `.agents/skills/methodology-copilot/SKILL.md` | **Classic interview** — paradigm refraction → RQs → `intent.json` → compile `protocol.json` + render `SCREENING_CRITERIA.md`. |
| `inception-agent` | `.agents/skills/inception-agent/SKILL.md` | **Grounded conversation driver** — runs the recon lifecycle (probe → distill → anchored directions) and delegates emission to the other two. |

This folder documents their boundaries (`01_skill_boundaries.md`), the concrete
handoff contracts between them (`02_handoffs.md`, including the `GENESIS` /
`recon_context` provenance contract), and the dual skill-tree topology +
distribution policy (`03_skill_tree_and_plugin_distribution.md`).

## Document map

| Doc | Scope |
| :--- | :--- |
| [`01_skill_boundaries.md`](./01_skill_boundaries.md) | Responsibilities, boundaries, and sequencing of the three orchestrator skills; how they compose the `scholar-*` kit skills and the `scholar-harness inception` wizard fast paths. |
| [`02_handoffs.md`](./02_handoffs.md) | Handoff contracts: scaffold → intent → compile → audit; the `GENESIS`/`recon_context` provenance contract (Windows-argv-safe); grounded delegation; who writes what, when. |
| [`03_skill_tree_and_plugin_distribution.md`](./03_skill_tree_and_plugin_distribution.md) | Dual-tree topology (`skills/` canonical vs `plugins/…/skills/` bundle), canonical-source rule, sync procedure, bundled vs excluded skills, and verification. |

## Non-goals

- This folder is **not** a re-specification of the grounded recon subsystem
  (that lives in `specs/exploratory-grounding-agent/` — `13_evaluation.md`,
  `14_agent_loops.md`, `16_inception_improvements.md`).
- It is **not** a replacement for the deep reference docs bundled with each
  skill (`references/`): those stay the authority for schema details
  (`intent_generator_spec.md`, `audit_trace_spec.md`, `tool_routing_matrix.md`, …).