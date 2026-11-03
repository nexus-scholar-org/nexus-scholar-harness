---
name: milestone
description: Start or resume a production-plan milestone (M0..M5) — branch from main, declare the lane, write the milestone status file with its DoD checklist and evidence table. Use when the user says "start M1", "resume M2", or "/milestone M3".
---

# /milestone <M>

The plan is `docs/roadmap/production-plan.md`; §6 holds each milestone's content,
definition of done (DoD) and lane. Its decisions are recorded in `docs/decisions.md`.

## Start

1. Confirm the work tree is clean (`git status --short`). If not, stop and ask.
2. Read the milestone row in plan §6, plus the plan sections it depends on
   (§1 findings for backend items, §2–§4 for UI items, §5 for packaging).
3. Create the branch from an up-to-date `main`:
   `git fetch origin main` then `git switch -c dev/<m>/<short-slug> origin/main`
   (lowercase milestone id, e.g. `dev/m1/screening-core`).
4. Write `docs/roadmap/milestones/<M>.md`:

```markdown
# <M> <title>
Branch: dev/<m>/<slug> · Lane: STANDARD|RELEASE (from plan §6; escalate per
docs/architecture/test_gate_policy.md) · Status: IN PROGRESS · Started: <date>

## Definition of done
- [ ] <one line per DoD item from plan §6, each naming its test or check>

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |

## Decisions
<links to docs/decisions.md entries made in this milestone>

## Evidence
| Stage | Commit | Command | Result | Duration |

## Deferred
<anything cut, with the plan §7 rule that allowed it>
```

5. Create a task list with one task per DoD item and say which you start with.

## Working rules

- Before fixing an assessment finding, use the `phase-auditor` agent on it, then
  write the reproducing test first and see it fail.
- Before UI work on a screen, its spec in `docs/ux/<phase>/final/` must be
  `Status: FINAL`; use the `ux-spec-writer` agent to produce drafts and ask the
  researcher to close open questions.
- After each executable edit run `/gate inner`; at the end of each DoD item run
  `/gate checkpoint`. Record checkpoint and pr results in the Evidence table.
- Every architectural choice gets a `docs/decisions.md` entry.
- A golden-workspace step that changes `workspaces/` must also append to that
  workspace's `audit/journal.jsonl` (see the `workspace-manager` skill).
- Contract drift (`generate_contract_baseline.py --check` fails) is
  `BLOCKED_BASELINE_DRIFT`: stop and ask; never regenerate to bless it.

## Resume

Read `docs/roadmap/milestones/<M>.md`, `git log --oneline origin/main..HEAD`, and
`git status`; report the unchecked DoD items and continue with the first one.

Finish with `/ship <M>`.
