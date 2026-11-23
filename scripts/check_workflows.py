"""Check the GitHub Actions workflows without running them (the local gate for `.github/**`).

What a local check can see: the YAML parses; every job has `runs-on` (or calls a reusable
workflow) and steps; every step has `uses` or `run`; every `needs` names a job of the same
workflow and the jobs form no cycle; every `actions/*` and `astral-sh/*` reference carries a
version; an artifact a job downloads is uploaded by a job it needs. What only a real run shows:
that the actions and their inputs exist at those versions, the runners' tools, caches and timing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def _needs(job: dict[str, Any]) -> list[str]:
    needs = job.get("needs", [])
    return [needs] if isinstance(needs, str) else list(needs)


def _ancestors(jobs: dict[str, Any], name: str) -> set[str]:
    seen: set[str] = set()
    stack = list(_needs(jobs[name]))
    while stack:
        current = stack.pop()
        if current in seen or current not in jobs:
            continue
        seen.add(current)
        stack.extend(_needs(jobs[current]))
    return seen


def check_workflow(path: Path) -> list[str]:
    problems: list[str] = []
    where = path.relative_to(ROOT).as_posix()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"{where}: does not parse: {exc}"]
    if not isinstance(data, dict):
        return [f"{where}: not a mapping"]
    # YAML 1.1 reads the bare key `on` as True.
    if "on" not in data and True not in data:
        problems.append(f"{where}: no `on` trigger")
    jobs = data.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        return [*problems, f"{where}: no jobs"]
    uploads: dict[str, set[str]] = {}
    for name, job in jobs.items():
        if not isinstance(job, dict):
            problems.append(f"{where}: job {name} is not a mapping")
            continue
        for need in _needs(job):
            if need not in jobs:
                problems.append(f"{where}: job {name} needs unknown job {need}")
        if "uses" in job:
            continue
        if "runs-on" not in job:
            problems.append(f"{where}: job {name} has no runs-on")
        steps = job.get("steps")
        if not isinstance(steps, list) or not steps:
            problems.append(f"{where}: job {name} has no steps")
            continue
        for index, step in enumerate(steps, 1):
            if not isinstance(step, dict) or not ({"uses", "run"} & step.keys()):
                problems.append(f"{where}: job {name} step {index} has neither uses nor run")
                continue
            uses = step.get("uses")
            if isinstance(uses, str) and not uses.startswith("./") and "@" not in uses:
                problems.append(f"{where}: job {name} step {index} uses {uses} without a version")
            if isinstance(uses, str) and uses.startswith("actions/upload-artifact"):
                artifact = (step.get("with") or {}).get("name")
                if artifact:
                    uploads.setdefault(str(artifact), set()).add(name)
    for name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        if name in _ancestors(jobs, name):
            problems.append(f"{where}: job {name} depends on itself")
        for index, step in enumerate(job.get("steps") or [], 1):
            uses = step.get("uses") if isinstance(step, dict) else None
            if isinstance(uses, str) and uses.startswith("actions/download-artifact"):
                artifact = (step.get("with") or {}).get("name")
                if artifact and not (uploads.get(str(artifact), set()) & _ancestors(jobs, name)):
                    problems.append(
                        f"{where}: job {name} step {index} downloads {artifact}, which no job it needs uploads"
                    )
    return problems


def main() -> int:
    files = sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")])
    if not files:
        print(f"ERROR: no workflow under {WORKFLOWS}")
        return 2
    problems = [problem for path in files for problem in check_workflow(path)]
    for problem in problems:
        print(f"ERROR: {problem}")
    if problems:
        return 1
    print(f"OK: {len(files)} workflows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
