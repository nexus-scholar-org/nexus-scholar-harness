# Follow-up Review Prompt — Harness Full-Picture Rating, Vision & Agent Blueprint

Copy this whole file into the reviewer agent's prompt. It builds directly on the
completed sweep review (verdict: **READY**) and asks for a **strategic**, repo-grounded
assessment — not another bug hunt.

---

## Mission

Three deliverables, in order:

1. **Rate the harness as a whole.** A holistic, evidence-cited scorecard of the Nexus
   Scholar Harness *as a system today* — architecture, reliability, automation depth,
   operator friendliness, distribution readiness — not a re-review of the 5 commits.
2. **Give your vision + directions.** Where should the harness go next, and the
   concrete directions worth pursuing, prioritized by impact / effort / risk.
3. **Define new agents to create.** Concrete agent definitions that would operationalize
   the highest-value directions, written in the same format the repo already uses for
   agents (see `.opencode/agent/*.md`), with explicit boundaries against what exists.

You are read-only. You never edit files; you produce a **report**, and for agents you
produce **definitions and complete file drafts** (as embedded code blocks) for a human
to drop in later.

## Working context (already-established facts — trust these, verify only if surprising)

- Repo: `C:\Users\mouadh\Documents\nexus-scholar-harness`. Windows/PowerShell; run
  everything via `uv run`. Read `AGENTS.md` first.
- Current health gates (measured 2026-09-13): pytest **248 passed / 3 skipped / 0
  failures** · `ruff check scripts/` clean · skill bundle sync `--check` **11/11 OK**.
- The just-completed sweep review rated the last 5 commits **READY for PR**, with a
  single NIT: `scholar-verify` `cli.py:3` docstring references an unregistered `ingress`
  command.
- Known-broken / weak MCP tooling (from `docs/kits_surface_matrix.md`, independently
  verified): 0-edge `nexus_graph_build` (server.py:436), `nexus_extract_pdf` drops
  metadata (server.py:302), `nexus_bib_clean` lint-only (server.py:469),
  `nexus_screen` never writes `conflicts.json`/`prisma_report.json` (server.py:278-284),
  `nexus_verify_claims` schema-mismatches RAG `claims.json`, and third `nexus_rag_query`
  cannot graph-boost. Phase-4 verify streams are CLI-only. MCP tools default to
  CWD-relative paths under `tools/scholar-agent-kit/`.
- Scale: **18 MCP tools** across 8 kits (15 `nexus_*` + 3 `recon_*`); agent-in-the-loop
  PRISMA screening is a file handoff (`agent_screen.py prepare|…|collect`); 11 skills
  mirrored canonical→bundle by `scripts/sync_skills_bundle.py`.

## Read these first (the strategic payload)

| Path | Why |
| :-- | :-- |
| `docs/kits_surface_matrix.md` | The verified API·CLI·MCP map + all failure modes. Your factual anchor. |
| `docs/README.md`, `README.md`, `AGENTS.md` | Repo self-description, doc index, conventions. |
| `docs/UPCOMING_WORK.md` | Live roadmap + backlog (supersedes the old phase-0…4 assessment). |
| `docs/phase_5/README.md` (+ `BLUEPRINT.md`, `PLAN.md`, `SPECS.md`) | Deferred thin **Harness Console** (agent-agnostic, local-first). |
| `docs/phase_6/README.md`, `docs/phase_7_distribution/README.md` | Trust bridge + deferred zero-friction distribution (uvx/any-harness). |
| `specs/inception-ecosystem/` (README + 01/02/03) | Skill-stack boundaries, handoffs, plugin-bundle policy. |
| `specs/exploratory-grounding-agent/` (README, `13_evaluation.md`, `14_agent_loops.md`, `10_task_list.md`) | The recon/inception subsystem, evaluation gates, agent loops, open tasks. |
| `.agents/skills/*/SKILL.md` | What agents know how to do today, per domain. |
| `.opencode/agent/*.md` | Existing agent personas (`coder`, `explore`, `general`, `reviewer`, `tester`, `inception-agent`) — the format + permission conventions to follow. |
| `tools/*/src/` structure + `src/scholar_harness/` | The actual system shape (thin orchestrator + kits). |

Skim phase docs for direction cues only; **do not re-derive the sweep findings** —
cite `docs/kits_surface_matrix.md` for those.

## Deliverable 1 — Full-picture rating

Scorecard with 0–10 per dimension, each score with ≥3 concrete, file:line-cited
evidences (strengths + weaknesses), then an overall weighted assessment:

1. **Architecture** — thin-orchestrator + 8 kit packages + MCP front-door: cohesion,
   seams, dependency hygiene (note undeclared deps, e.g. rag↔protocol, agent↔verify).
2. **Reliability** — the known-broken MCP tooling, silent error swallowing, CWD-relative
   defaults, Phase-4 CLI-only gap; how much does it erode agent trust today?
3. **Automation depth** — what is genuinely agent-driven (inception, screening handoff,
   recon) vs. what still needs a human (Phase-4 streams, graph, conflict adjudication).
4. **Operability & DX** — onboarding (workspaces empty, snapshot restore), docs quality,
   skill mirror hygiene, test-opacity of kit CLIs.
5. **Distribution readiness** — Phase-7 deferred; what's missing (plugin manifest is
   minimal, mcp_config has no env, version pins unpinned to hashes).
6. **Test & contract confidence** — 248 passing, but how much *conformance* testing ties
   the matrix/skills to code? (Is the surface matrix assertion-free markdown?)

**Overall verdict** paragraph: one honest sentence capturing where the harness is today.

## Deliverable 2 — Vision & directions

- **Vision**: 3–5 paragraph forward vision (12–24 months) — what the harness becomes,
  who uses it, how agents + humans interact with it end-to-end. Must stay compatible
  with the documented constraints: agent-agnostic CLI+MCP+file-first, thin orchestrator
  (never absorb kit logic), append-only audit, fork+PR contribution gate.
- **Directions**: rank 6–10 concrete directions. For each: **outcome**, **why now**
  (tie to a scorecard weakness or an existing deferred block), **effort** (S/M/L),
  **risk**, **first concrete step** (one command or one file to create), and whether it
  should happen **before** or **inside** the Phase-5/Phase-7 blocks.
  - Must-consider candidates to evaluate (rank honestly, don't rubber-stamp): fixing the
    broken MCP tools; a conformance-test suite driven by the surface matrix; the
    `ingress` NIT + Phase-4 console actions; a screening-orchestrator agent; Phase-5
    console; Phase-7 distribution; recon-saturation surfacing into screening.
  - Include at least one direction outside the current roadmap that you think the repo
    is *uniquely positioned* to win at.

## Deliverable 3 — Agent definitions (the core ask)

Design **3–6 new agents** that operationalize your top directions. Each definition must
be **non-overlapping** with the existing 6 and with each other (table the overlaps and
how you resolve them). Follow the `agent.md` frontmatter format already in
`.opencode/agent/` (name, description, temperature/model, `tools` permissions, feature
flags). For each agent provide:

- **Name + one-line mandate** (e.g. "prisma-steward").
- **Scope & responsibilities** — exact tasks, inputs, and file-handoff contracts
  (which files it reads/writes; which audit events it logs).
- **Tools & permissions** — exact subset of the 18 MCP tools + CLIs it may call, and
  what it must NEVER do (e.g. no direct `git push`; the pull-request-gate rule).
- **Skills it loads** — from the existing 11 SKILL.md, plus any new skill it needs.
- **Human/agent handoffs** — what it waits on, what it initiates, failure recovery.
- **DoD / test** — how the repo will know the agent works (hermetic test, fixture, or
  smoke command).
- **Effort** — S/M/L to stand up.

Prefer agents that close *real* loops found in the review (e.g. conflict
adjudication, Phase-4 verification, conformance/QA, graph/rag analysis, distribution
packaging, workspace hygiene). Flag which are "now", "after the fix-the-tooling wave",
and "with Phase-5/Phase-7".

## Report format

```
# Harness Full-Picture Rating, Vision & Agent Blueprint
## 1. Rating            (scorecard table + verdict)
## 2. Vision            (paragraphs)
## 3. Directions        (ranked table, then each expanded)
## 4. Agent blueprint   (overlap matrix, then one full definition per agent,
                        with a ready-to-paste .opencode/agent/<name>.md draft
                        in a fenced YAML-frontmatter code block)
## 5. Prioritized rollout  (phase-now / phase-later mapping)
```

## Constraints

- Read-only: locate and cite, never modify/commit/push.
- Every business-direction claim must be grounded in a repo fact (file:line or measured
  output). Mark speculative vision as explicitly speculative.
- Respect existing decisions: thin orchestrator, agent-agnostic surface, append-only
  audit, fork+PR gate, `workspaces/`-only output rule.
- No generic consultant filler — every recommendation must name the concrete repo change.