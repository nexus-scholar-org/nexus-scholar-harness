"""Select deterministic test commands from the repository gate manifest."""

from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "architecture" / "test_gate_manifest.json"


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").removeprefix("./")


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
    docs = data.get("docs", {})
    if not isinstance(docs, dict):
        raise ValueError("manifest docs section must be an object")  # noqa: TRY004
    consumed = docs.get("consumed", {})
    if not isinstance(consumed, dict) or not all(
        isinstance(pattern, str)
        and isinstance(commands, list)
        and commands
        and all(isinstance(command, str) for command in commands)
        for pattern, commands in consumed.items()
    ):
        raise ValueError(
            "manifest docs.consumed must map glob patterns to non-empty command lists"
        )
    excluded = docs.get("consumed_excluded", [])
    if not isinstance(excluded, list) or not all(
        isinstance(name, str) for name in excluded
    ):
        raise ValueError("manifest docs.consumed_excluded must be a list of names")
    locked = docs.get("locked", [])
    if not isinstance(locked, list) or not all(
        isinstance(pattern, str) for pattern in locked
    ):
        raise ValueError("manifest docs.locked must be a list of glob patterns")
    locked_commands = docs.get("locked_commands", [])
    if not isinstance(locked_commands, list) or not all(
        isinstance(command, str) for command in locked_commands
    ):
        raise ValueError("manifest docs.locked_commands must be a list of commands")
    return data


def matching_tasks(data: dict[str, Any], paths: list[str]) -> list[str]:
    normalized = [normalize_path(path) for path in paths]
    matches: set[str] = set()
    for task_id, task in data["tasks"].items():
        for path in normalized:
            if any(fnmatch.fnmatchcase(path, pattern) for pattern in task["paths"]):
                matches.add(task_id)
    return sorted(matches, key=lambda value: int(value.split("-")[1]))


def is_prose_doc(path: str) -> bool:
    """Pure-prose candidates: markdown anywhere, or anything under docs/.

    Consumption, not extension or directory, decides the gate — callers must
    check consumed/locked matches first. A prose path takes the light gate
    (common commands only) and never the full suite on its own.
    """
    lowered = path.lower()
    return lowered.endswith(".md") or path == "docs" or path.startswith("docs/")


def match_consumed(data: dict[str, Any], paths: list[str]) -> list[str]:
    """Boundary commands for docs consumed by tests/packaging/generators."""
    docs = data.get("docs", {})
    consumed = docs.get("consumed", {})
    excluded = docs.get("consumed_excluded", [])
    commands: list[str] = []
    for path in paths:
        if any(f"/{name}/" in f"/{path}/" for name in excluded):
            # Mirror-excluded skills (e.g. pull-request-gate: sync EXCLUDED and
            # count-freshness SYNC_EXCLUDED) are contributor prose, not
            # consumed surfaces.
            continue
        for pattern, pattern_commands in consumed.items():
            if fnmatch.fnmatchcase(path, pattern):
                for command in pattern_commands:
                    if command not in commands:
                        commands.append(command)
    return commands


def match_locked(data: dict[str, Any], paths: list[str]) -> list[str]:
    """Drift commands for baseline-locked non-executable docs."""
    docs = data.get("docs", {})
    locked = docs.get("locked", [])
    locked_commands = docs.get("locked_commands", [])
    if any(fnmatch.fnmatchcase(path, pattern) for path in paths for pattern in locked):
        return list(locked_commands)
    return []


def path_is_task_matched(data: dict[str, Any], path: str) -> bool:
    return any(
        fnmatch.fnmatchcase(path, pattern)
        for task in data["tasks"].values()
        for pattern in task["paths"]
    )


def fallback_repositories(paths: list[str]) -> set[str]:
    """Infer conservative owning repositories for unmatched executable paths."""
    repos: set[str] = set()
    for raw_path in paths:
        path = normalize_path(raw_path)
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
    normalized = [normalize_path(path) for path in paths]
    consumed_commands = match_consumed(data, normalized)
    locked_commands = match_locked(data, normalized)
    if (
        not selected
        and not inferred_fallbacks
        and not consumed_commands
        and not locked_commands
        and not normalized
    ):
        raise ValueError(
            "no task selected; pass --task or a path matching the manifest"
        )

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
    covered_docs = _covered_doc_paths(data, normalized)
    unknowns = [
        path
        for path in normalized
        if (
            not path_is_task_matched(data, path)
            and not fallback_repositories([path])
            and path not in covered_docs
            and not is_prose_doc(path)
        )
    ]
    if unknowns:
        # Unknown surface: conservative harness full-suite fallback, even when
        # other paths selected a narrower gate (union, never light-only).
        for command in data["fallback"]["harness"]:
            if command not in commands:
                commands.append(command)
    for command in (*consumed_commands, *locked_commands):
        if command not in commands:
            commands.append(command)
    return ordered_tasks, commands


def _covered_doc_paths(data: dict[str, Any], normalized: list[str]) -> set[str]:
    """Paths already carrying a docs boundary (consumed or locked match)."""
    docs = data.get("docs", {})
    consumed = docs.get("consumed", {})
    excluded = docs.get("consumed_excluded", [])
    locked = docs.get("locked", [])
    covered: set[str] = set()
    for path in normalized:
        if any(f"/{name}/" in f"/{path}/" for name in excluded):
            continue
        if any(fnmatch.fnmatchcase(path, pattern) for pattern in consumed):
            covered.add(path)
        if any(fnmatch.fnmatchcase(path, pattern) for pattern in locked):
            covered.add(path)
    return covered


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
