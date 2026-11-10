# Phase 0 inception: UX review and wireframes (2026-11-02)

UX and methodology review of the grounded inception module
(`src/scholar_harness/inception/`), the recon engine (`src/scholar_harness/recon/`),
the `inception-agent` skill and its parity helper, with wireframes for a revised flow.

Status: **proposal**. Code-reading review by an AI reviewer (Claude); no user testing.
As of 2026-11-10 this review and its wireframes are history. The build source is the final specs in [`final/`](final/): 01 and 04 to 08 are built (M4b, PR #209); 02 Explore and 03 Direction are DRAFT and not built, although recon over HTTP exists (M4c, PR #210).
Line references point to the code as of 2026-11-02.

## Where things are

| Item | Live (private, share from its Share menu) | Source in this folder |
| :-- | :-- | :-- |
| Referee-style review | https://claude.ai/artifact/FZENQRHeKSQD7WwqmsLEhy | [`review.html`](review.html) (artifact page body; the host adds the `<html>` skeleton) |
| Wireframe canvas, 11 boards | https://claude.ai/artifact/Dwo4z3mZQjqejCcgMs9SH2 | [`wireframes/`](wireframes/) (`canvas.json` + one `.dc.html` per board) |

The `.dc.html` files are Design-canvas components; they render inside the canvas
editor, not as standalone pages. To edit, open the live canvas or republish these
sources to it.

## Boards

| # | File | Shows |
| :-- | :-- | :-- |
| 1 | `Main.dc.html` | One six-step flow (Scope, Explore, Direction, Shape, Concepts, Review) shared by both front ends |
| 2 | `Wizard.dc.html` | CLI wizard: step header, marked defaults, plain pool health, concept checklist with a visible check budget |
| 3 | `Agent.dc.html` | Chat agent: one decision per turn with quick replies, live brief panel, write gate |
| 4 | `Review.dc.html` | Review and emit: full intent with Edit links and the exact files to be written |
| 5 | `States.dc.html` | No direction, thin pool, unanchored term, empty narrower search, resume draft |
| 6 | `StepScope.dc.html` | Step 1: years, languages, search mode and sample size set before the first search |
| 7 | `StepExplore.dc.html` | Step 2: pool health, schools, topics, metrics, paper list |
| 8 | `StepGap.dc.html` | Step 3 (optional): gap check on a scant / sparse / dense scale |
| 9 | `StepShape.dc.html` | Step 4: paradigm cards, playbook, unit, proof, RQ draft |
| 10 | `StepCriteria.dc.html` | Step 5: criteria with their source, matrix columns, Phase-4 checks, criteria preview |
| 11 | `StepDone.dc.html` | Done: files written, GENESIS logged, Phase-1 search hand-off |

## UX findings

| # | Finding | Code | Status |
| :-- | :-- | :-- | :-- |
| 1 | Re-search option printed as `__delta_probe__` | `grounded.py` | Fixed, `46f4a46` |
| 2 | Skill default limit 10 sat below `POOL_THIN_FLOOR` 12 | `gates.py:23`, skill | Fixed, `46f4a46` |
| 3 | Probe runs from 2000 in keyword mode; date window asked later | `engine.py:268`, `wizard.py` | Designed (board 6) |
| 4 | Unanchored concept exits the whole wizard after ~15 answers | `grounded.py:448` | Designed (boards 2, 5) |
| 5 | Grounded default concepts unbounded; one synonym prompt per concept | `grounded.py:400` | Designed (board 2) |
| 6 | Default not shown in choices; 180-column refraction grid | `wizard.py:92`, `display.py:22` | Default fixed `46f4a46`; grid designed (board 9) |
| 7 | Narrower search with no result was silent | `grounded.py:342` | Fixed, `46f4a46` |
| 8 | Pre-emit panel shows counts only, no way back | `wizard.py:338` | Designed (board 4) |
| 9 | Pool health reported as purity / QEI jargon | `grounded.py` | Designed (boards 2, 7) |
| 10 | Session id formats differ between wizard and MCP | `grounded.py:281` | Open |

The fixes in `46f4a46` were made on branch `fix/inception-ux-quick-wins` and are on `main` (checked 2026-11-10).

## Methodology comments (from the review)

| # | Comment | Severity | Needs |
| :-- | :-- | :-- | :-- |
| M1 | Unanchored synonyms are dropped, which hurts recall | Major | Methodological decision |
| M2 | Directions are frequent phrases on thin, query-shaped evidence | Major | Design decision |
| M3 | Gate thresholds (12 papers, 0.50 purity) calibrated on one trial | Major | Multi-field validation |
| M4 | Semantic results drift; provider, date, mode not in the protocol | Major | Contract v1 gate (touches `protocol.json`) |
| M5 | No multi-database choice, PRESS review, criteria pilot, dual screening, registration | Major | Roadmap |
| M6 | Four keyword-detected paradigms; no PICO / SPIDER / PEO | Moderate | Design decision |
| M7 | Three machine-ranked directions can steer the researcher | Moderate | Design decision |

## Next work

1. Build the wireframe fixes that need no contract change: scope before the probe,
   re-prompt instead of a hard exit, capped concept defaults, full pre-emit summary,
   paradigm cards, one session-id format.
2. Decide M1 and M4 (M4 goes through the Contract v1 gate).
3. Run short sessions with two or three PhD students and one supervisor to test the UX judgements.
