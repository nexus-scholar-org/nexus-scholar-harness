"""Select deterministic test commands from the repository gate manifest."""

from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "architecture" / "test_gate_manifest.json"


def load_manifest() -> dict[str, Any]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    required = {"schema_version", "stages", "common", "tasks", "fallback"}
    missing = sorted(required - data.keys())
    if missing:
        raise ValueError(f"manifest missing keys: {missing}")
    stages = data["stages"]
    if stages != ["inner", "checkpoint", "pr", "closure"]:
        raise ValueError("manifest stages must be inner, checkpoint, pr, closure")
    for task_id, task in data["tasks"].items():
        if not task_id.startswith("T-"):
            raise ValueError(f"invalid task ID: {task_id}")
        for key in ("repo", "paths", *stages):
            if key not in task:
                raise ValueError(f"{task_id} missing {key}")
        if not task["paths"]:
            raise ValueError(f"{task_id} has no path selectors")
    return data


def matching_tasks(data: dict[str, Any], paths: list[str]) -> list[str]:
    normalized = [path.replace("\\", "/").lstrip("./") for path in paths]
    matches: set[str] = set()
    for task_id, task in data["tasks"].items():
        for path in normalized:
            if any(fnmatch.fnmatchcase(path, pattern) for pattern in task["paths"]):
                matches.add(task_id)
    return sorted(matches, key=lambda value: int(value.split("-")[1]))


def fallback_repositories(paths: list[str]) -> set[str]:
    """Infer conservative owning repositories for unmatched executable paths."""
    repos: set[str] = set()
    for raw_path in paths:
        path = raw_path.replace("\\", "/").lstrip("./")
        if path.startswith("tools/scholar-rag-kit/"):
            repos.add("scholar-rag-kit")
        elif path.startswith("tools/scholar-agent-kit/"):
            repos.add("scholar-agent-kit")
        elif path.startswith(("src/", "scripts/", "tests/", ".github/", "packaging/")) or path in {
            "pyproject.toml",
            "uv.lock",
        }:
            repos.add("harness")
    return repos


def select_commands(
    data: dict[str, Any], *, tasks: list[str], paths: list[str], stage: str
) -> tuple[list[str], list[str]]:
    selected = set(tasks)
    selected.update(matching_tasks(data, paths))
    unknown = sorted(selected - data["tasks"].keys())
    if unknown:
        raise ValueError(f"unknown tasks: {', '.join(unknown)}")
    inferred_fallbacks = fallback_repositories(paths)
    if not selected and not inferred_fallbacks:
        raise ValueError("no task selected; pass --task or a path matching the manifest")

    ordered_tasks = sorted(selected, key=lambda value: int(value.split("-")[1]))
    commands: list[str] = []
    for command in data["common"][stage]:
        if command not in commands:
            commands.append(command)
    task_commands: list[str] = []
    for task_id in ordered_tasks:
        for command in data["tasks"][task_id][stage]:
            if command not in commands:
                commands.append(command)
                task_commands.append(command)
    if not task_commands:
        repos = {data["tasks"][task_id]["repo"] for task_id in ordered_tasks}
        repos.update(inferred_fallbacks)
        for repo in sorted(repos):
            for command in data["fallback"].get(repo, data["fallback"]["harness"]):
                if command not in commands:
                    commands.append(command)
    return ordered_tasks, commands


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", action="append", default=[], help="task ID, repeatable")
    parser.add_argument("--path", action="append", default=[], help="changed path, repeatable")
    parser.add_argument(
        "--stage", choices=("inner", "checkpoint", "pr", "closure"), default="inner"
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--check", action="store_true", help="validate the manifest only")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        data = load_manifest()
        if args.check:
            print(f"OK: {len(data['tasks'])} tasks, {len(data['stages'])} stages")
            return 0
        tasks, commands = select_commands(
            data, tasks=args.task, paths=args.path, stage=args.stage
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2

    if args.format == "json":
        print(json.dumps({"stage": args.stage, "tasks": tasks, "commands": commands}, indent=2))
    else:
        print(f"stage={args.stage} tasks={','.join(tasks)}")
        print("\n".join(commands))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
