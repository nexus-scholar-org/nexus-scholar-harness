# Onboarding: the production plan in one page

For a developer joining the project. It explains the plan and gives a reading
order. It does not assign work; that comes after you have read it.

> Everything linked here is on `main`. The plan arrived in PR
> [#183](https://github.com/nexus-scholar-org/nexus-scholar-harness/pull/183)
> and the design canvases in PR
> [#182](https://github.com/nexus-scholar-org/nexus-scholar-harness/pull/182).

## What we are building

Nexus Scholar is a tool for systematic literature reviews. It ships as one
Python package (`nexus-scholar`) with a FastAPI engine and a Next.js research UI
(`apps/research-ui`). The goal for the next two months is to bring three phases
to production:

- **Phase 0, Inception:** turn a research question into a protocol.
- **Phase 1, Discovery:** search databases and build a deduplicated corpus.
- **Phase 2, Screening:** a human decides include, exclude or unclear for each
  record, on desktop or phone, with full provenance.

**Screening comes first** and is what ships at week 6. Discovery is stretch, and
the web Inception wizard comes after the two months; until then inception runs
through the CLI and MCP, labelled beta. Everything else (synthesis, graph, RAG,
risk of bias) is parked and labelled "not production" rather than removed.

Principles that shape every decision:
- **Local first.** The engine runs on the researcher's machine; reviews are
  private and unpublished. No hosted service in stage 1.
- **The human decides.** The AI only proposes. Its proposal is hidden until the
  researcher has decided, and by default the researcher sees every record.
- **Everything is auditable.** Every significant step is appended to the
  workspace's `audit/journal.jsonl`, and every decision carries provenance.

## Milestones

| Milestone | Week | What it delivers |
| :-- | :-- | :-- |
| M0 Foundations | 1 | Security fixes for the console, brand theme and dark mode, golden workspace, `accept-corpus` (the entry path into screening) |
| M1a Screening backend | 2–3 | Decision events, approval per batch, proposal store, the screening API |
| M1b Desktop UI + AI driver | 4 | Desktop triage with keyboard, the Anthropic driver, publish with phone pairing |
| M2 Mobile | 5 | Swipe screening on a phone over the local network, offline queue and replay |
| M5-slim Package | 6 | Installable wheel serving the UI, decision export, methods paragraph. **The gate:** a real end-to-end screening run on the golden UAV workspace |
| M3 Discovery | 7–8 | Stretch |

M1a and M1b meet at a written API contract with shared test fixtures, so the
backend and the UI can be built at the same time by two people.

## Reading order

**1. The plan and why (start here, about 45 minutes)**
1. [`production-plan.md`](production-plan.md): scope, audit of the current
   code, specs, theme, mobile, deployment, and §6 milestones with their
   definition of done.
2. [`../decisions.md`](../decisions.md): one short entry per decision, newest
   first. Read the 2026-11-03 and 2026-11-04 entries.
3. [`../assessment/README.md`](../assessment/README.md): the evidence-backed
   list of known defects (IDs such as CON-10, INC-01) that milestones fix.

**2. The screening design (what gets built first)**
4. [`../architecture/screening-api-contract.md`](../architecture/screening-api-contract.md):
   the boundary between engine and UI. Decision events, every endpoint,
   refusal codes, shared fixtures, and the decisions in §9.
5. Screen specs, all FINAL, in
   [`../ux/phase2-screening/final/`](../ux/phase2-screening/final/):
   [01 home](../ux/phase2-screening/final/01-screening-home.md),
   [02 prepare](../ux/phase2-screening/final/02-prepare.md),
   [03 desktop triage](../ux/phase2-screening/final/03-triage-desktop.md),
   [04 mobile triage](../ux/phase2-screening/final/04-triage-mobile.md),
   [05 record detail](../ux/phase2-screening/final/05-record-detail.md),
   [06 agent proposals](../ux/phase2-screening/final/06-agent-proposals-run.md),
   [07 agreement](../ux/phase2-screening/final/07-agreement-with-agent.md),
   [08 states](../ux/phase2-screening/final/08-states.md),
   [09 publish](../ux/phase2-screening/final/09-publish.md).
6. [`../architecture/agent-system.md`](../architecture/agent-system.md): how
   the AI works behind each phase (versioned tasks, proposals, validators, the
   prompt gate, cost and privacy).
7. [`../ux/brand/BRAND_BOOK.md`](../ux/brand/BRAND_BOOK.md): the design system
   the UI is themed with. The wireframe canvases (Claude Design files) are in
   `docs/ux/phase{0,1,2}/final/project/`.

**3. Rules of the repository (before your first change)**
8. [`../../AGENTS.md`](../../AGENTS.md): setup, layout, conventions and the
   development workflow. Read the "Setup" and "Development workflow" sections.
9. [`../architecture/DEVELOPER_COMPASS.md`](../architecture/DEVELOPER_COMPASS.md)
   and [`../architecture/contract_v1_baseline.md`](../architecture/contract_v1_baseline.md):
   the frozen data contract. Its check must pass in every PR and is never
   regenerated to hide a change.
10. [`../architecture/test_gate_policy.md`](../architecture/test_gate_policy.md):
    which tests to run when. Small edits run only their area's tests; the full
    suite runs once per PR.
11. [`../../.agents/skills/pull-request-gate/SKILL.md`](../../.agents/skills/pull-request-gate/SKILL.md):
    how changes ship (fork, then PR; never push branches to `origin`).

**Optional:** [`../architecture/refusals.md`](../architecture/refusals.md)
(typed refusal codes), [`../kits_surface_matrix.md`](../kits_surface_matrix.md)
(the CLI and MCP surface of each package),
[`../nexus_scholar_user_guide.md`](../nexus_scholar_user_guide.md)
(using the tool).

## Getting it running

```bash
uv sync --extra dev --extra pdf --extra rag
```

```bash
uv run python scripts/select_test_gate.py --changed main --stage inner
```

```bash
uv run python scripts/generate_contract_baseline.py --check
```

For the UI: `cd apps/research-ui`, then `npm install` and `npm test`.

## How work is done

- One branch per milestone (`dev/<milestone>/<slug>`) from `main`, one PR per
  milestone through the fork.
- Each task declares a test lane (FAST, STANDARD or RELEASE) before work starts.
- Each milestone gets a status file in `docs/roadmap/milestones/` (created when
  the milestone starts) with its definition-of-done checklist and test
  evidence; that checklist is the task list.
- Claude Code commands in `.claude/skills/` (`/milestone`, `/gate`, `/ship`)
  and review agents in `.claude/agents/` support this workflow; using them is
  optional.

## Questions to bring back

After reading, note anything unclear or that you disagree with, especially in
the screening contract. Contract changes are cheap now and expensive after M1a.
