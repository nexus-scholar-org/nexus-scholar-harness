"""Build the golden screening workspace from the v0.3 UAV review (M0).

The golden workspace is the end-to-end quality gate of the production plan:
the researcher screens these 30 records through the product, and
``scripts/check_golden_workspace.py`` verifies the result. This script makes
its contents reproducible:

1. the protocol, intent and rendered criteria are copied unchanged from the
   source workspace (``uav-crop-weed-v03``, protocol v0.3, frozen 2026-10-29);
2. 30 records are selected deterministically from the source's screening
   batches, in three strata: 10 the agents included, 15 clear exclusions
   spread over exclusion reasons, and 5 borderline exclusions (third-lane or
   second-pass);
3. ``literature/verified.json`` and ``golden_selection.json`` are written and
   each step is journalled.

The source decisions are agent decisions that no human has confirmed. They are
used only to choose a varied sample; they are not copied as labels, and the
golden run starts with no decisions at all.

Run it on a workspace scaffolded with ``nexus-scholar init --scaffold-only``,
then run ``nexus-scholar accept-corpus`` on the result.

    uv run python scripts/build_golden_workspace.py \
        --source workspaces/uav-crop-weed-v03 --dest workspaces/golden-uav-30
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from scholar_harness.workspace.audit import append_event

ROOT = Path(__file__).resolve().parents[1]

STRATA = (("agent_include", 10), ("clear_exclude", 15), ("borderline_exclude", 5))
COPIED = ("protocol.json", "protocol.sha256", "intent.json", "SCREENING_CRITERIA.md")


def _order(workspace_id: str) -> str:
    return hashlib.sha256(workspace_id.encode("utf-8")).hexdigest()


def _stratum(decision: dict) -> str | None:
    lane = decision.get("lane")
    if decision["decision"] == "INCLUDE":
        return "agent_include"
    if lane == "mutual_exclude":
        return "clear_exclude"
    if lane in ("third_lane", "pass2"):
        return "borderline_exclude"
    return None  # not_retrieved: no abstract to screen


def _load_source(source: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    papers: dict[str, dict] = {}
    decisions: dict[str, dict] = {}
    screening = source / "literature" / "screening"
    for batch in sorted(screening.glob("batch_[0-9][0-9][0-9].json")):
        for paper in json.loads(batch.read_text(encoding="utf-8"))["papers"]:
            papers[paper["workspace_id"]] = paper
        decided = batch.with_name(f"{batch.stem}_decisions.json")
        for row in json.loads(decided.read_text(encoding="utf-8"))["decisions"]:
            decisions[row["workspace_id"]] = row
    return papers, decisions


def _pick(decisions: dict[str, dict], papers: dict[str, dict]) -> list[tuple[str, str]]:
    by_stratum: dict[str, list[dict]] = {name: [] for name, _ in STRATA}
    for workspace_id, row in decisions.items():
        stratum = _stratum(row)
        if stratum and (papers.get(workspace_id, {}).get("abstract") or "").strip():
            by_stratum[stratum].append(row)

    chosen: list[tuple[str, str]] = []
    for name, count in STRATA:
        rows = sorted(by_stratum[name], key=lambda r: _order(r["workspace_id"]))
        if name == "clear_exclude":
            # Round-robin over exclusion reasons so the sample is not all one kind.
            groups: dict[str, list[dict]] = {}
            for row in rows:
                groups.setdefault(row.get("reason_code") or "UNSPECIFIED", []).append(row)
            ordered, codes = [], sorted(groups)
            while len(ordered) < len(rows):
                for code in codes:
                    if groups[code]:
                        ordered.append(groups[code].pop(0))
            rows = ordered
        if len(rows) < count:
            raise SystemExit(f"stratum {name}: only {len(rows)} usable records, need {count}")
        chosen.extend((row["workspace_id"], name) for row in rows[:count])
    return chosen


def _verified_row(paper: dict) -> dict:
    return {
        "workspace_id": paper["workspace_id"],
        "title": paper["title"],
        "year": paper.get("year"),
        "provider": paper.get("provider") or "unknown",
        "provider_id": paper.get("doi") or paper["workspace_id"],
        "external_ids": {"doi": paper["doi"]} if paper.get("doi") else {},
        "abstract": paper.get("abstract"),
    }


def build(source: Path, dest: Path) -> list[tuple[str, str]]:
    if not (dest / "project.json").is_file():
        raise SystemExit(f"{dest} is not a workspace; run `nexus-scholar init --scaffold-only` first")
    if (dest / "literature" / "verified.json").exists():
        raise SystemExit(f"{dest}/literature/verified.json already exists; refusing to overwrite")

    for name in COPIED:
        shutil.copyfile(source / name, dest / name)
    protocol = json.loads((dest / "protocol.json").read_text(encoding="utf-8"))
    manifest_path = dest / "project.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["description"] = (
        "Golden screening workspace: 30 records from uav-crop-weed-v03 under its "
        "frozen v0.3 protocol. The quality gate for the production plan."
    )
    manifest["research_questions"] = [
        rq.get("text", "") if isinstance(rq, dict) else str(rq)
        for rq in protocol.get("research_questions", [])
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    append_event(
        dest,
        "PROTOCOL_ADOPTED",
        f"Adopted the frozen v0.3 protocol from {source.name} unchanged",
        inputs=[f"{source.name}/{name}" for name in COPIED],
        outputs=list(COPIED),
        parameters={"source_workspace": source.name},
    )

    papers, decisions = _load_source(source)
    chosen = _pick(decisions, papers)
    rows = [_verified_row(papers[workspace_id]) for workspace_id, _ in chosen]
    literature = dest / "literature"
    literature.mkdir(exist_ok=True)
    (literature / "verified.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    selection = {
        "schema": "golden-selection-v1",
        "source_workspace": source.name,
        "rule": "per stratum, records with an abstract ordered by sha256(workspace_id); "
        "clear exclusions round-robin over reason_code",
        "note": "Strata come from unconfirmed agent decisions and are used only to "
        "choose a varied sample. They are not labels.",
        "records": [{"workspace_id": w, "stratum": s} for w, s in chosen],
    }
    (dest / "golden_selection.json").write_text(json.dumps(selection, indent=2), encoding="utf-8")
    counts = {name: sum(1 for _, s in chosen if s == name) for name, _ in STRATA}
    append_event(
        dest,
        "CORPUS_SELECTED",
        f"Selected {len(chosen)} records from {source.name} for the golden run",
        inputs=[f"{source.name}/literature/screening/batch_*.json"],
        outputs=["literature/verified.json", "golden_selection.json"],
        parameters={"rule": selection["rule"]},
        metrics={"records": len(chosen), **counts},
    )
    return chosen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=ROOT / "workspaces" / "uav-crop-weed-v03")
    parser.add_argument("--dest", type=Path, default=ROOT / "workspaces" / "golden-uav-30")
    args = parser.parse_args()
    chosen = build(args.source.resolve(), args.dest.resolve())
    print(f"Selected {len(chosen)} records into {args.dest}")


if __name__ == "__main__":
    main()
