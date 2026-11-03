---
name: ship
description: Close a milestone — final PR gate once, contract check, independent review, then push to the fork and open the PR to origin per the pull-request gate. Use when the user says "ship M1" or "/ship M1".
---

# /ship <M>

Pushing and opening a PR are outward-facing: get the researcher's explicit yes
in chat before step 5, unless they already said to ship in this request.

1. **DoD:** read `docs/roadmap/milestones/<M>.md`. Every DoD box is checked or
   listed under "Deferred" with its plan §7 rule. Otherwise stop and report.
2. **Gate once:** `/gate pr` on the final executable commit. Then
   `uv run python scripts/generate_contract_baseline.py --check` and
   `git diff --check origin/main...HEAD`. Record the results in Evidence.
   A failure here means fix, commit, and re-run `/gate pr`.
3. **Review:** run the `milestone-reviewer` agent with `<M>` and base `main`.
   On CHANGES, fix only the listed findings, re-run the smallest load-bearing
   test (and `/gate pr` only if executable code changed), then re-review with
   the previous findings. On BLOCKED, stop and ask the researcher.
4. **Close the file:** set `Status: READY FOR PR` in the milestone file and
   commit it with the rest of the branch.
5. **Push and PR:** load and follow `.agents/skills/pull-request-gate/SKILL.md`.
   Push to `fork` only (`git push -u fork <branch>`); never to `origin`, never
   `--no-verify`. Open the PR with
   `gh pr create -R nexus-scholar-org/nexus-scholar-harness --base main --head nexus-scholar:<branch>`.
   The PR body states: milestone and plan link, lane, DoD checklist, findings
   fixed (with test names), the Evidence table, reviewer verdict, what was not
   verified, and the attribution line required for this session.
6. Report the PR URL and what remains for the next milestone.
