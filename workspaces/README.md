# Workspaces

Research project workspaces live here. Each project gets its own folder
(`workspaces/<project-slug>/`) with a canonical file contract — `protocol.json`,
`intent.json`, `SCREENING_CRITERIA.md`, `INDEX.md`, `project.json`,
`audit/journal.jsonl`, plus `literature/`, `pdfs/`, `extracted/`,
`synthesis/`, `phase4/`.

All prior workspace content was removed from the working tree on
**2026-09-11** to return the repo to a clean, empty state. Everything is still
recoverable from git history:

- Full snapshot with all workspaces populated: `72090e5` (see
  [`docs/COMMIT_SNAPSHOTS.md`](../docs/COMMIT_SNAPSHOTS.md)).
- Restore a single workspace from HEAD before emptying, e.g.
  `git checkout 72090e5 -- workspaces/uav-cv-precision-agriculture`.

## Creating a new workspace

Workspaces are scaffolded dynamically by the harness — do not hand-create one:

```bash
uv run scholar-harness inception --root .   # Socratic wizard → protocol.json + SCREENING_CRITERIA.md
uv run scholar-harness status  -w workspaces/<slug>
uv run scholar-harness sync    -w workspaces/<slug>
```