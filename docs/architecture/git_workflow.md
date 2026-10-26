# Git Workflow — Multi-Branch Staging

## AUTONOMOUS MODE

All git operations are pre-approved. No human approval required for:
- Creating branches
- Switching branches
- Committing changes
- Merging branches
- Deleting branches
- Tagging releases

Execute the full workflow without pausing.

## Branch Strategy

```
main (production)
  └── staging/phase-{X} (phase integration)
       └── dev/phase-{X}/task-{N} (active development)
```

## Branch Naming

| Branch Type | Pattern | Example | Purpose |
|-------------|---------|---------|---------|
| Production | `main` | `main` | Stable release |
| Phase Staging | `staging/phase-{X}` | `staging/phase-a` | Phase integration testing |
| Task Dev | `dev/phase-{X}/task-{N}` | `dev/phase-a/task-3` | Active task development |

## Workflow Commands

### 1. Start New Phase

```bash
# Create staging branch from main
git checkout main
git pull origin main
git checkout -b staging/phase-{X}

# Create first task branch
git checkout -b dev/phase-{X}/task-1 staging/phase-{X}
```

### 2. Task Development

```bash
# Start task (already on dev branch)
# ... implement task ...

# Run targeted tests
uv run pytest tests/{relevant_files}.py -v

# Commit task
git add {files}
git commit -m "feat(phase-{X}): implement task {N} - {title}"

# Merge to staging
git checkout staging/phase-{X}
git merge --no-ff dev/phase-{X}/task-{N}
git branch -d dev/phase-{X}/task-{N}

# Create next task branch
git checkout -b dev/phase-{X}/task-{N+1} staging/phase-{X}
```

### 3. Phase Completion

```bash
# Run full test suite
uv run pytest tests/ -x
uv run ruff check scripts/
uv run pytest tests/conformance/ -v

# Merge staging to main
git checkout main
git merge --no-ff staging/phase-{X}
git tag -a v{X}.0.0 -m "Phase {X} complete"
git branch -d staging/phase-{X}
```

### 4. Hotfix (if needed)

```bash
# Create hotfix branch
git checkout -b hotfix/{issue} main

# Fix and test
uv run pytest tests/{affected}.py -v

# Merge to main and staging
git checkout main
git merge --no-ff hotfix/{issue}
git checkout staging/phase-{X}
git merge --no-ff hotfix/{issue}
git branch -d hotfix/{issue}
```

## Commit Message Format

```
feat(phase-{X}): {description}

- {change 1}
- {change 2}

Task: {N}
Files: {list}
```

## Branch Protection Rules

| Branch | Requires Review | Requires Tests | Requires CI |
|--------|----------------|----------------|-------------|
| `dev/*` | No | No | No |
| `staging/*` | No | Yes | Yes |
| `main` | Yes | Yes | Yes |

## Phase Progression

| Phase | Branch | Status | Dependencies |
|-------|--------|--------|--------------|
| 0 | `staging/phase-0` | DONE | None |
| A | `staging/phase-a` | PENDING | Phase 0 |
| B | `staging/phase-b` | PENDING | Phase 0 |
| C | `staging/phase-c` | PENDING | Phase 0 |
| D | `staging/phase-d` | PENDING | Phase 0, A |
| E | `staging/phase-e` | PENDING | Phase B, D |
| F | `staging/phase-f` | PENDING | Phase D |

## Conflict Resolution

When merging task branches:
1. Prefer rebasing over merging for clean history
2. Resolve conflicts in the task branch before merging
3. Never force-push to `staging/*` or `main`

## Tags

| Tag Pattern | Meaning | Example |
|-------------|---------|---------|
| `v{X}.0.0` | Phase complete | `v0.0.0`, `v1.0.0` |
| `v{X}.{Y}.0` | Task complete | `v1.1.0`, `v1.2.0` |
| `v{X}.{Y}.{Z}` | Hotfix | `v1.1.1` |
