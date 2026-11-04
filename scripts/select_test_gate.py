"""Select deterministic test commands from the repository gate manifest."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "architecture" / "test_gate_manifest.json"
AREA_PATHS_TOKEN = "{area_paths}"


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
    areas = data.get("areas", [])
    if not isinstance(areas, list):
        raise ValueError("manifest areas must be a list")  # noqa: TRY004
    defaults = data.get("area_defaults", {})
    names: set[str] = set()
    for area in areas:
        name = area.get("name")
        if not isinstance(name, str) or not name or name in names:
            raise ValueError(f"area name missing or duplicated: {name!r}")
        names.add(name)
        if not area.get("paths"):
            raise ValueError(f"area {name} has no path selectors")
        for stage in stages:
            if not (area.get(stage) or defaults.get(stage)):
                raise ValueError(f"area {name} has no {stage} commands")
    return data


def area_for_path(data: dict[str, Any], path: str) -> dict[str, Any] | None:
    """First matching area wins; specific areas precede catch-alls."""
    for area in data.get("areas", []):
        if any(fnmatch.fnmatchcase(path, pattern) for pattern in area["paths"]):
            return area
    return None


def is_test_file(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return path.startswith("tests/") and name.startswith("test_") and name.endswith(".py")


def area_commands(
    data: dict[str, Any], area: dict[str, Any], stage: str, area_paths: list[str]
) -> list[str]:
    commands = area.get(stage) or data.get("area_defaults", {}).get(stage, [])
    root = area.get("path_root", "")
    relative = " ".join(path.removeprefix(root) for path in area_paths)
    return [command.replace(AREA_PATHS_TOKEN, relative) for command in commands]


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
        if path.startswith(("src/scholar_rag/", "tests/kits/rag/")):
            repos.add("scholar-rag-kit")
        elif path.startswith(("src/scholar_agent/", "tests/kits/agent/")):
            repos.add("scholar-agent-kit")
        elif path.startswith(("src/", "scripts/", "tests/", ".github/")) or path in {
            "pyproject.toml",
            "uv.lock",
        }:
            repos.add("harness")
    return repos


def partition_paths(
    data: dict[str, Any], paths: list[str]
) -> tuple[dict[str, list[str]], list[str], list[str]]:
    """Split paths into area hits, changed test files, and the rest.

    Markdown never takes an area gate (it is prose or a consumed/locked doc).
    A changed test file outside every area runs itself; anything else falls
    through to the E3 task rules and the conservative fallback.
    """
    hits: dict[str, list[str]] = {}
    test_files: list[str] = []
    rest: list[str] = []
    for path in paths:
        area = None if path.lower().endswith(".md") else area_for_path(data, path)
        if area is not None:
            hits.setdefault(area["name"], []).append(path)
        elif is_test_file(path):
            test_files.append(path)
        else:
            rest.append(path)
    order = [area["name"] for area in data.get("areas", [])]
    return {name: hits[name] for name in order if name in hits}, test_files, rest


def matched_areas(data: dict[str, Any], paths: list[str]) -> list[str]:
    hits, _, _ = partition_paths(data, [normalize_path(path) for path in paths])
    return list(hits)


def select_commands(
    data: dict[str, Any], *, tasks: list[str], paths: list[str], stage: str
) -> tuple[list[str], list[str]]:
    all_paths = [normalize_path(path) for path in paths]
    hits, test_files, paths = partition_paths(data, all_paths)
    selected = set(tasks)
    selected.update(matching_tasks(data, paths))
    unknown = sorted(selected - data["tasks"].keys())
    if unknown:
        raise ValueError(f"unknown tasks: {', '.join(unknown)}")
    inferred_fallbacks = fallback_repositories(paths)
    normalized = paths
    consumed_commands = match_consumed(data, all_paths)
    locked_commands = match_locked(data, all_paths)
    if (
        not selected
        and not inferred_fallbacks
        and not consumed_commands
        and not locked_commands
        and not all_paths
    ):
        raise ValueError(
            "no task selected; pass --task or a path matching the manifest"
        )

    ordered_tasks = sorted(selected, key=lambda value: int(value.split("-")[1]))
    commands: list[str] = []
    for command in data["common"][stage]:
        if command not in commands:
            commands.append(command)
    by_name = {area["name"]: area for area in data.get("areas", [])}
    for name, area_paths in hits.items():
        for command in area_commands(data, by_name[name], stage, area_paths):
            if command not in commands:
                commands.append(command)
    if test_files:
        if stage == "inner":
            own = [f"uv run pytest {' '.join(test_files)} -q"]
        elif stage == "checkpoint":
            # The file's own directory; a top-level tests/test_*.py runs itself.
            targets: list[str] = []
            for path in test_files:
                parent = path.rsplit("/", 1)[0]
                target = path if parent == "tests" else parent
                if target not in targets:
                    targets.append(target)
            own = [f"uv run pytest {' '.join(targets)} -q"]
        else:
            own = data.get("area_defaults", {}).get(stage) or data["fallback"]["harness"]
        for command in own:
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
    return ordered_tasks, drop_subsumed_pytest(commands)


FULL_SUITE_COMMANDS = ("uv run pytest -q", "uv run pytest -q -n auto")


def drop_subsumed_pytest(commands: list[str]) -> list[str]:
    """Run the full Python suite once: it subsumes every narrower pytest run.

    Narrower runs carry no extra options beyond paths, ``-q`` and ``-m``, so the
    full suite (which includes slow tests) covers them. One full-suite command
    is kept, the parallel one when both were selected.
    """
    full = [command for command in commands if command in FULL_SUITE_COMMANDS]
    if not full:
        return commands
    keep = "uv run pytest -q -n auto" if "uv run pytest -q -n auto" in full else full[0]
    result: list[str] = []
    for command in commands:
        if command.startswith("uv run pytest"):
            if command == keep and keep not in result:
                result.append(command)
            continue
        result.append(command)
    return result


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
        "--changed",
        nargs="?",
        const="main",
        default=None,
        metavar="BASE",
        help="add every path changed since the merge base with BASE (default main), "
        "including staged, unstaged and untracked files",
    )
    parser.add_argument(
        "--stage", choices=("inner", "checkpoint", "pr", "closure"), default="inner"
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--check", action="store_true", help="validate the manifest only")
    return parser.parse_args()


def changed_paths(base: str) -> list[str]:
    """Paths changed since the merge base with ``base``, plus the work tree."""

    def git(*args: str) -> list[str]:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    merge_base = git("merge-base", base, "HEAD")[0]
    found: list[str] = []
    for listing in (
        git("diff", "--name-only", merge_base),
        git("diff", "--name-only", "--cached"),
        git("ls-files", "--others", "--exclude-standard"),
    ):
        for path in listing:
            if path not in found:
                found.append(path)
    return found


def main() -> int:
    args = parse_args()
    try:
        data = load_manifest()
        if args.check:
            print(
                f"OK: {len(data['tasks'])} tasks, {len(data.get('areas', []))} areas, "
                f"{len(data['stages'])} stages"
            )
            return 0
        paths = list(args.path)
        if args.changed is not None:
            paths.extend(path for path in changed_paths(args.changed) if path not in paths)
            if not paths and not args.task:
                print(f"stage={args.stage} areas= tasks=\nno changes since {args.changed}")
                return 0
        tasks, commands = select_commands(
            data, tasks=args.task, paths=paths, stage=args.stage
        )
        areas = matched_areas(data, paths)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}")
        return 2

    if args.format == "json":
        print(
            json.dumps(
                {
                    "stage": args.stage,
                    "areas": areas,
                    "tasks": tasks,
                    "paths": paths,
                    "commands": commands,
                },
                indent=2,
            )
        )
    else:
        print(f"stage={args.stage} areas={','.join(areas)} tasks={','.join(tasks)}")
        print("\n".join(commands))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
