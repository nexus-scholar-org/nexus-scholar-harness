# Commit Snapshots

Known-good commits bookmarked so they can be restored later. Each entry records
what was in the tree at that point and how to return to it.

---

## Snapshot 1 — Pre-cleanup baseline

| Field | Value |
| :-- | :-- |
| **Short hash** | `72090e5` |
| **Full hash** | `72090e5c0e561e4517ed50da507d29fc361abf12` |
| **Date** | 2026-09-10 07:37:01 +0100 |
| **Author** | nexus-scholar `<bekhouche.mouadh@univ-oeb.dz>` |
| **Subject** | `chore(latex): remove superseded header.tex (preamble now inline in main.tex)` |
| **Pushed** | Yes — `origin/main` pointed at this commit |
| **Bookmarked** | 2026-09-11, immediately before the repo cleanup commit |

### What this snapshot contains

This is the last commit that still tracked the following non-harness material,
which was removed in the cleanup that followed:

- `brainstorming/` — 25 architecture/strategy deep-dive markdowns (Phases 0–4, methodology tooling, product/website strategy).
- `notebooks/` — 4 tutorial Jupyter notebooks for the research workflow.
- `docs/reports/` — `KIT_VERSION_REPORT.md`, `REFACTOR_SUMMARY.md`, `SKILLS_UPGRADE_SUMMARY.md`.
- `compute_kappa.py`, `check_kit_versions.py`, `verify_skills_upgrade.py` — one-off dev scripts at the repo root.

All of the above remain reachable through this commit (and git history), even
after deletion from the working tree.

### How to return to it

```bash
# Inspect files as they were (read-only)
git checkout 72090e5 -- <path>

# Full temporary checkout (detached HEAD)
git checkout 72090e5c0e561e4517ed50da507d29fc361abf12

# Recreate a branch from the snapshot
git switch -c baseline-72090e5 72090e5c0e561e4517ed50da507d29fc361abf12
```

> Research workspaces under `workspaces/` (e.g. `uav-cv-precision-agriculture`,
> `ai-research-harnesses-trust`) are present at this snapshot and were **not**
> part of the cleanup.
