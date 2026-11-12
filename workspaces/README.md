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
  [`docs/internal/COMMIT_SNAPSHOTS.md`](../docs/internal/COMMIT_SNAPSHOTS.md)).
- Restore a single workspace from HEAD before emptying, e.g.
  `git checkout 72090e5 -- workspaces/uav-cv-precision-agriculture`.

## Workspaces kept in the repository

- `golden-uav-30`: the committed starting point of the golden screening run. The
  end-to-end test copies it; never commit a run into it.
- `golden-uav-30-run-2026-11-06`: the evidence of the golden run of 2026-11-06.
- `uav-crop-weed-v03`: the human-confirmed screening set (protocol v0.3) that the
  prompt gate and the golden fixture are built from.

## Workspaces removed on 2026-11-12

`uav-crop-weed-reliability` (the v0.2 pilot) and `uav-pilot-demo` (the v0.2
demonstration rerun, with the 2026-10-16 harvest calibration files that
`docs/lessons/2026-10-17_uav_harvest_calibration_lessons.md` cites) were removed
at the researcher's request. Documents that name them describe the tree as it
was. Both are complete at commit `0ede974c`:

```bash
git checkout 0ede974c -- workspaces/uav-pilot-demo
git checkout 0ede974c -- workspaces/uav-crop-weed-reliability
```

## Creating a new workspace

Workspaces are scaffolded dynamically by the harness — do not hand-create one:

```bash
uv run scholar-harness inception --root .   # Socratic wizard → protocol.json + SCREENING_CRITERIA.md
uv run scholar-harness status  -w workspaces/<slug>
uv run scholar-harness sync    -w workspaces/<slug>
```