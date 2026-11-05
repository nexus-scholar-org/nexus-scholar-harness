"""Verdict on a finished golden screening run (M0; the M5-slim gate).

Three checks, each read from the workspace's own files:

- **journal**: ``audit/journal.jsonl`` parses line by line and records every
  stage of the run, in order: workspace created, protocol in place, corpus
  accepted, batches prepared, decisions recorded, screening published.
- **provenance**: in the newest accepted ``screening_decisions`` artifact of
  each batch, every decision has method ``HUMAN``, a real screener id (not empty or
  ``*-draft``) and a real ``decided_at`` (not empty or 1970), and every study of the
  accepted corpus snapshot has exactly one decision.
- **prisma**: ``literature/prisma_report.json`` reconciles with the corpus
  snapshot (records identified, duplicates, studies screened) and with the
  published ``included.json``, ``excluded.json`` and ``conflicts.json``.

    uv run python scripts/check_golden_workspace.py workspaces/golden-uav-30

Exit code 0 when every check passes, 1 otherwise. ``--json`` prints the
results as JSON instead of a table.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

#: Journal stages in run order: (name, accepted actions, artifact_type or None).
STAGES: tuple[tuple[str, frozenset[str], str | None], ...] = (
    ("workspace created", frozenset({"PROJECT_INITIALIZED", "GENESIS"}), None),
    ("protocol in place", frozenset({"GENESIS", "PROTOCOL_ADOPTED", "PROTOCOL_AMENDED"}), None),
    ("corpus accepted", frozenset({"ARTIFACT_ACCEPTED"}), "corpus_snapshot"),
    ("batches prepared", frozenset({"ARTIFACT_ACCEPTED"}), "screening_batch"),
    ("decisions recorded", frozenset({"SCREENING_DECISIONS_RECORDED"}), None),
    ("screening published", frozenset({"SCREENING_GENERATION_PUBLISHED"}), None),
)


@dataclass
class CheckResult:
    name: str
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _registry(ws: Path) -> dict[str, dict]:
    path = ws / "audit" / "artifact_registry.json"
    if not path.is_file():
        return {}
    return _read_json(path).get("artifacts", {})


def _latest(registry: dict[str, dict], artifact_type: str) -> list[tuple[str, dict]]:
    items = [(k, e) for k, e in registry.items() if e.get("artifact_type") == artifact_type]
    return sorted(items, key=lambda item: item[1].get("accepted_at", ""))


def _corpus(ws: Path, registry: dict[str, dict]) -> dict | None:
    corpora = _latest(registry, "corpus_snapshot")
    if not corpora:
        return None
    return _read_json(ws / corpora[-1][1]["path"])["data"]


def check_journal(ws: Path) -> CheckResult:
    result = CheckResult("journal")
    path = ws / "audit" / "journal.jsonl"
    if not path.is_file():
        result.problems.append("audit/journal.jsonl is missing")
        return result
    events: list[dict] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            result.problems.append(f"line {number} is not JSON: {exc.msg}")
    position = -1
    for name, actions, artifact_type in STAGES:
        found = next(
            (
                i
                for i, event in enumerate(events)
                if i > position
                and event.get("action") in actions
                and event.get("status", "SUCCESS") == "SUCCESS"
                and (
                    artifact_type is None
                    or (event.get("parameters") or {}).get("artifact_type") == artifact_type
                )
            ),
            None,
        )
        if found is None:
            result.problems.append(f"no '{name}' event after the previous stage")
        else:
            position = found
    return result


def check_provenance(ws: Path) -> CheckResult:
    result = CheckResult("provenance")
    registry = _registry(ws)
    corpus = _corpus(ws, registry)
    if corpus is None:
        result.problems.append("no accepted corpus_snapshot in the registry")
        return result
    newest_per_batch: dict[str, dict] = {}
    for _, entry in _latest(registry, "screening_decisions"):
        data = _read_json(ws / entry["path"])["data"]
        newest_per_batch[data["batch_id"]] = data
    if not newest_per_batch:
        result.problems.append("no accepted screening_decisions artifact")
        return result

    decided: dict[str, int] = {}
    for data in newest_per_batch.values():
        for decision in data["decisions"]:
            study = decision["study_id"]
            decided[study] = decided.get(study, 0) + 1
            if decision.get("method") != "HUMAN":
                result.problems.append(
                    f"{study}: method {decision.get('method')!r}, not HUMAN"
                )
            # DEVELOPER_COMPASS §6: a real screener and a real time, not the
            # CON-11 placeholders (`researcher-draft`, the 1970 epoch).
            screener = str(decision.get("screener_id") or "")
            if not screener or screener.endswith("-draft"):
                result.problems.append(f"{study}: placeholder screener {screener!r}")
            decided_at = str(decision.get("decided_at") or "")
            if not decided_at or decided_at.startswith("1970-"):
                result.problems.append(f"{study}: placeholder decided_at {decided_at!r}")
    studies = {study["study_id"] for study in corpus["studies"]}
    for study in sorted(studies - set(decided)):
        result.problems.append(f"{study}: no decision")
    for study, count in sorted(decided.items()):
        if count > 1:
            result.problems.append(f"{study}: {count} decisions across batches")
        if study not in studies:
            result.problems.append(f"{study}: decided but not in the corpus snapshot")
    return result


def check_prisma(ws: Path) -> CheckResult:
    result = CheckResult("prisma")
    literature = ws / "literature"
    path = literature / "prisma_report.json"
    if not path.is_file():
        result.problems.append("literature/prisma_report.json is missing (not published)")
        return result
    prisma = _read_json(path)
    corpus = _corpus(ws, _registry(ws))

    def expect(field_name: str, actual: int, what: str) -> None:
        if prisma.get(field_name) != actual:
            result.problems.append(f"{field_name} is {prisma.get(field_name)}, {what} gives {actual}")

    if corpus is not None:
        records = len(corpus["record_to_study"])
        studies = len(corpus["studies"])
        expect("total_identified", records, "the corpus snapshot")
        expect("duplicates_removed", records - studies, "the corpus snapshot")
        expect("records_screened", studies, "the corpus snapshot")
    included = int(prisma.get("records_included") or 0)
    unclear = int(prisma.get("records_unclear") or 0)
    excluded = int(prisma.get("records_excluded") or 0)
    files: dict[str, int] = {}
    for name in ("included.json", "excluded.json", "conflicts.json"):
        file = literature / name
        if not file.is_file():
            result.problems.append(f"literature/{name} is missing")
        else:
            files[name] = len(_read_json(file))
    # Unclear (MAYBE) is forwarded to full text with the includes (decision
    # 2026-11-04), so included.json holds both.
    if "included.json" in files and files["included.json"] != included + unclear:
        result.problems.append(
            f"records_included + records_unclear is {included + unclear}, "
            f"included.json gives {files['included.json']}"
        )
    if "excluded.json" in files:
        expect("records_excluded", files["excluded.json"], "excluded.json")
    if "conflicts.json" in files:
        expect("conflicts_flagged", files["conflicts.json"], "conflicts.json")
    # Conflicts are borderline rows flagged for audit; they are also partitioned,
    # so they are a subset of the screened records, not an extra bucket.
    if included + unclear + excluded != prisma.get("records_screened"):
        result.problems.append(
            f"included + unclear + excluded = {included + unclear + excluded}, "
            f"records_screened is {prisma.get('records_screened')}"
        )
    # A record breaking several criteria counts once under each reason.
    breakdown = prisma.get("exclusion_reasons_breakdown") or {}
    if breakdown and sum(breakdown.values()) < excluded:
        result.problems.append(
            f"exclusion reasons sum to {sum(breakdown.values())}, fewer than "
            f"records_excluded ({excluded})"
        )
    return result


def run_checks(workspace: Path | str) -> list[CheckResult]:
    ws = Path(workspace).resolve()
    return [check_journal(ws), check_provenance(ws), check_prisma(ws)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--json", action="store_true", help="print the results as JSON")
    args = parser.parse_args(argv)
    results = run_checks(args.workspace)
    if args.json:
        print(json.dumps([{**asdict(r), "ok": r.ok} for r in results], indent=2))
    else:
        for r in results:
            print(f"{'PASS' if r.ok else 'FAIL'}  {r.name}")
            for problem in r.problems:
                print(f"      - {problem}")
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
