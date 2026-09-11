---
name: pull-request-gate
description: Enforce the fork + pull-request contribution gate for the Nexus Scholar Harness. Use whenever the user asks to git push, git commit, merge, branch, pull request, PR, push to origin/github, fork, or make (or ask to prepare / prepare and push) a change to the repo. Remembers the 2026-09-11 decision: all improvements ship through the personal fork and a PR to nexus-scholar-org/nexus-scholar-harness — never by direct push to origin.
---

# Pull-request-gate

## The decision (binding, 2026-09-11)

Direct pushes of feature/improvement branches to `origin` are **forbidden**.
Every improvement must go through the **personal fork** and land via a **pull
request** to the canonical repo. Only `main` on `origin` may be pushed directly
(housekeeping baseline). Never bypass this gate.

## Remotes

| Name | URL | Purpose |
| :-- | :-- | :-- |
| `origin` | `https://github.com/nexus-scholar-org/nexus-scholar-harness` | Canonical repo. Direct pushes of `main` only. |
| `fork` | `https://github.com/nexus-scholar/nexus-scholar-harness` | Your personal fork. All improvement branches live here. |

## Non-negotiable rules

1. **Never push a feature branch to `origin`.** Create the branch, commit, run
   `uv run pytest` (must pass) and `uv run ruff check scripts/`, then push to
   `fork` and open a PR to `origin`.
2. **Never force-push** to `origin`. If a history rewrite is essential, do it
   on the fork, never on the canonical repo.
3. Only `main` may be pushed directly to `origin`, and only for explicit
   housekeeping the human authorizes.
4. Pushing to the fork (`git push fork <branch>`) is always allowed.

## Standard flow

```bash
# 1. Branch off main
git switch -c feat/your-improvement main

# 2. Change + verify
uv run pytest          # must pass
uv run ruff check scripts/

# 3. Commit to the branch
git add <paths>
git commit -m "feat(scope): summary"

# 4. Push to your fork
git push fork feat/your-improvement

# 5. Open the PR against the canonical repo
gh pr create -R nexus-scholar-org/nexus-scholar-harness \
  --base main --head nexus-scholar:feat/your-improvement
```

If you are told to just work without PRs, ask the human to confirm the fork
workflow before pushing to `origin`.

---

## Enforcement hook (installed)

A `pre-push` hook blocks direct feature pushes to `origin`. It is tracked at
`scripts/hooks/pre-push` and enabled with:

```bash
git config core.hooksPath scripts/hooks
```

If the hook ever blocks a push you must **not** bypass it —
`git push --no-verify` or `-f` is disallowed for feature branches. Follow the
instructions the hook prints instead (push to fork → open PR).

**Restore / reinstall after a fresh clone:** `git config core.hooksPath scripts/hooks`.
