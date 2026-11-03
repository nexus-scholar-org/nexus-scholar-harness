# Phase 2 screening: UX review and wireframes (2026-11-02)

UX and methodology review of agent-in-the-loop PRISMA title/abstract screening:
`src/scholar_harness/agent_screen.py` and `src/scholar_harness/screening/`
(`batcher.py`, `worker.py`, `collector.py`, `integrity.py`, `report.py`), the review and
approval layer in `src/scholar_harness/authority/review.py`, and the checklist rule in
`tools/scholar-agent-kit/src/scholar_agent/calibration.py`, read against the SCR1 screening
lessons (27–54) in [UAV harvest calibration lessons](../../lessons/2026-10-17_uav_harvest_calibration_lessons.md).
Open-access PDF harvest (the other half of Phase 2) is out of scope here.

Status: **proposal**. Code-reading review by an AI reviewer (Claude); no user testing.
Line references point to the code as of 2026-11-02. Previous phase: [Phase 1 discovery](../phase1-discovery/README.md).

## Where things are

| Item | Live (private, share from its Share menu) | Source in this folder |
| :-- | :-- | :-- |
| Wireframe canvas, 8 boards + 11 finding notes | https://claude.ai/artifact/3xndtfxV5guaojzRGoJsnn | [`wireframes/`](wireframes/) (`canvas.json` + one `.dc.html` per board) |

The `.dc.html` files render inside the Design-canvas editor. All figures on the boards are
one internally consistent worked example (3,241 works); titles and DOIs are placeholders.
The boards were rendered and checked on 2026-11-02.

## Boards

| # | File | Shows |
| :-- | :-- | :-- |
| 1 | `Main.dc.html` | Six-step flow (Prepare, Calibrate, Screen, Triage, Agreement, Publish); where researcher time goes today vs redesign |
| 2 | `Prepare.dc.html` | Binding check, batch size, seeded shuffle, two blind lanes, three-state criteria with an Unclear outcome |
| 3 | `Calibrate.dc.html` | Lanes vs your own labels on 30 records; missed includes; suggested criterion fix |
| 4 | `Progress.dc.html` | Per-lane progress, running tallies, files validated and quarantined on arrival |
| 5 | `Triage.dc.html` | One queue of disagreements and both-include records; side-by-side checklists and verbatim reasoning; keyboard decisions |
| 6 | `Agreement.dc.html` | Raw agreement, kappa with prevalence, 2x2 table, disagreements by criterion |
| 7 | `States.dc.html` | Protocol changed, missing field, title only, shard failed, unclear rows, not approved |
| 8 | `Publish.dc.html` | PRISMA screening box, final checks, files written, one approval for the whole generation |

## Findings

| # | Finding | Code / evidence | Severity |
| :-- | :-- | :-- | :-- |
| S1 | No "unclear" outcome: include only if every inclusion box is true; a missing box counts as false; MAYBE refused at finalize. Title-only records lean to EXCLUDE, the reverse of "when in doubt, include" | `calibration.py:79,97`; `collector.py:857`; `batcher.py:359` | Major |
| S2 | **Bug:** on the checklist path the screener's reasoning is not passed to `checklist_to_decision`, so every decision is recorded as "Agent screened." | `collector.py:842`, `collector.py:928` | Major |
| S3 | Legacy files get invented defaults: missing decision → INCLUDE, missing confidence → 0.80 | `collector.py:851,871`; lesson 31 | Major |
| S4 | "Confidence" is a constant set by the rule (0.90 / 0.55 / 0.75), not a measurement | `calibration.py:109` | Major |
| S5 | Dual screening exists only through file names; no screener-2 prepare, status or agreement report | `collector.py:335`; lesson 35 | Major |
| S6 | Calibration falls back to a heuristic when no gold file is given | `agent_screen.py:79` | Moderate |
| S7 | `prepare` needs an accepted corpus snapshot; the Phase-1 hand-off does not explain how | `batcher.py:198` | Moderate |
| S8 | Batches follow corpus order, so provider blocks cluster | `batcher.py:266`; lesson 48 | Moderate |
| S9 | Review and approve are one batch at a time (~160 batches for 3,241 works) | `agent_screen.py` `--batch` | Moderate |
| S10 | Strengths: fingerprint binding, exact coverage, stale-binding refusal, worker never invents reasons, publication approval gate, refused files kept as `.rejected` | `integrity.py`, `worker.py`, `collector.py:821` | Keep |
| S11 | Status shows done/pending only; validity and reasons appear only at collect | `collector.py:59` | Minor |

## Where fixes belong

- **Harness (this repo):** S2 (pass `screening_reasoning` through; small, testable), S3 (refuse or
  record as debt instead of defaulting), S5 lanes and agreement report, S7 hand-off message,
  S8 seeded shuffle, S9 generation-level approval, S11 validation on arrival.
- **scholar-agent-kit (canonical repo, fork + PR):** S1 three-state checklist and an UNCLEAR
  outcome in `checklist_to_decision`, S4 confidence semantics.
- **Contract v1 gate:** an UNCLEAR / full-text-queue decision value touches
  `ScreeningDecisionValue` and the screening artifacts, so it needs an architecture decision,
  regenerated schemas and fixtures, and review before any code.
