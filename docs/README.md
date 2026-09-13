# Documentation Index

Authoritative index of this repository's documentation. The live operational
guide for agents is `AGENTS.md` at the repo root — read it first.

## Roadmap & backlog

| Doc | State | What |
| :-- | :-- | :-- |
| [`UPCOMING_WORK.md`](./UPCOMING_WORK.md) | **Live** | Consolidated outstanding-work & roadmap analysis; supersedes the phase-0…4 roadmap assessment (deleted 2026-09-13). |

## Design specs — Phase 0 (implemented)

Canonical design set for the Socratic inception engine and the `protocol.json`
contract (implemented in `src/scholar_harness/inception.py` + `scholar-protocol-kit`).
Index: [`phase_0/README.md`](./phase_0/README.md).

## Design specs — future phases

| Doc | Phase | State |
| :-- | :-- | :-- |
| [`phase_5/README.md`](./phase_5/README.md) | 5 · Harness Console (thin UI) | Design complete — not yet implemented |
| [`phase_6/README.md`](./phase_6/README.md) | 6 · Scientific trust & external-harness bridge | Partly implemented (`scholar-verify-kit`, `nexus_verify_claims`/`nexus_screen_reconcile`) |
| [`phase_7_distribution/README.md`](./phase_7_distribution/README.md) | 7 · Zero-friction, bench-portable distribution | Deferred 2026-09-09 |

## Operations

| Doc | What |
| :-- | :-- |
| [`COMMIT_SNAPSHOTS.md`](./COMMIT_SNAPSHOTS.md) | Known-good commits (`72090e5` snapshot, follow-up `80f7810`) for restoring removed material from git history. |
| [`kits_surface_matrix.md`](./kits_surface_matrix.md) | **Kit Surface Matrix** (API · CLI · MCP) — the agent-facing knowledge base of all eight kits: public API anchors, CLI surfaces, MCP wrappers with their behavior forks, cross-cutting failure modes (MCP CWD-poisoning, 0-edge `nexus_graph_build`, `nexus_verify_claims` schema mismatch, `nexus_extract_pdf` metadata loss, …), cross-kit dependency graph, env vars. |

## Specification series (living)

| Path | What |
| :-- | :-- |
| [`specs/exploratory-grounding-agent/`](../specs/exploratory-grounding-agent/README.md) | Grounded Exploratory Inception Agent — canonical spec folder (01…16 + `evaluation/`), with its own document map. |
| [`specs/inception-ecosystem/`](../specs/inception-ecosystem/README.md) | Inception skill stack (methodology-copilot / workspace-manager / inception-agent) — boundaries, handoffs, and the skill-tree + plugin-bundle distribution policy. |
| `.agents/skills/<kit>/SKILL.md` | Per-kit agent skills (`scholar-search`, `scholar-pdf`, `scholar-rag`, … , `inception-agent`, `methodology-copilot`, `workspace-manager`); mirror synced by `scripts/sync_skills_bundle.py`. |