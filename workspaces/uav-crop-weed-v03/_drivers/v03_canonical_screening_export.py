#!/usr/bin/env python3
"""Materialise the v0.3 calibration screening into the canonical screening layout.

The pilot produced its dual/pass-2/third-lane decisions under
``calibration_v03/screening_scr1/`` and then reconciled them into
``literature/screening/final_decisions.json``. The harness console and the
Research UI read the *canonical* layout instead::

    literature/screening/MANIFEST.json
    literature/screening/batch_001.json
    literature/screening/batch_001_decisions.json
    ...

This driver writes that derived view and nothing else. It is an **export**, not
a new screening run:

* the source batches, the 566 decision files, ``protocol.json``,
  ``final_decisions.json``, ``included.json`` and ``excluded.json`` are read
  only and are never rewritten;
* every emitted file carries a ``derived_export`` provenance block naming the
  source directory, the FINAL_AGENT_UNCONFIRMED decision status, the criteria
  hash that agreed the decisions, and the fact that no accepted corpus/artifact
  registry backs the batches (so the console reports coverage as unresolved
  rather than claiming an accepted parent it does not have);
* identifiers are copied from the source records; nothing is minted here.

Usage::

    uv run python workspaces/uav-crop-weed-v03/_drivers/v03_canonical_screening_export.py
    ... --workspace <dir> --force
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_WORKSPACE = SCRIPT_DIR.parent

SOURCE_DIR = Path("calibration_v03") / "screening_scr1"
DECISION_STATUS = "FINAL_AGENT_UNCONFIRMED"
HUMAN_CONFIRMATION = "PENDING (HumanConfirmation@1 unsigned)"
DEV_NOTE = (
    "Derived export of the v0.3 calibration screening for console/UI reading. "
    "Not a new screening run, not a Contract-v1 published generation, and not a "
    "human confirmation. The canonical dual-codefiles under "
    "calibration_v03/screening_scr1/ remain the authoritative record."
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_write(path: Path, payload: Any) -> None:
    tmp = path.with_name(path.name + f".tmp-{uuid.uuid4().hex[:8]}")
    tmp.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    os.replace(tmp, path)


def _criteria_bundle(protocol: dict[str, Any]) -> dict[str, Any]:
    """The criterion-refs read wants protocol.screening_criteria verbatim."""
    return {
        "title": (protocol.get("metadata") or {}).get("title", "Research Protocol"),
        "research_questions": protocol.get("research_questions", []),
        "screening_criteria": protocol.get("screening_criteria", {}),
    }


def _paper(record: dict[str, Any]) -> dict[str, Any]:
    """One canonical batch paper, copied from the screened record."""
    paper: dict[str, Any] = {
        "workspace_id": record["screening_id"],
        "title": record.get("title") or "",
    }
    if record.get("abstract"):
        paper["abstract"] = record["abstract"]
    if record.get("doi"):
        paper["doi"] = record["doi"]
    if record.get("year") is not None:
        paper["year"] = record["year"]
    if record.get("providers"):
        # `provider` is not part of the canonical paper shape, but it is the
        # stored provenance of the record's index source; kept as-is.
        paper["provider"] = record["providers"]
    return paper


def _decision(workspace_id: str, final: dict[str, Any]) -> dict[str, Any]:
    screening = final["screening"]
    provenance = final.get("screening_provenance") or {}
    entry: dict[str, Any] = {
        "workspace_id": workspace_id,
        "decision": screening["decision"],
        "confidence": screening.get("confidence"),
        "matched_inclusion_criteria": list(
            screening.get("matched_inclusion_criteria") or []
        ),
        "violated_exclusion_criteria": list(
            screening.get("violated_exclusion_criteria") or []
        ),
        "relevant_rqs": [],
        "screening_reasoning": screening.get("screening_reasoning") or "",
        # Not in the console writer's record, but both fields are the stored
        # bytes that explain *which lane* produced this decision; readers
        # tolerate extras and the UI shows neither as a claim.
        "reason_code": provenance.get("reason_code"),
        "lane": provenance.get("lane"),
    }
    if provenance.get("deviation"):
        entry["deviation"] = provenance["deviation"]
    return entry


def build(workspace: Path) -> tuple[dict[str, Any], list[tuple[Path, Any]]]:
    source_dir = workspace / SOURCE_DIR
    protocol = _read_json(workspace / "protocol.json")
    summary_path = workspace / "literature" / "screening" / "summary.json"
    final_path = workspace / "literature" / "screening" / "final_decisions.json"
    summary = _read_json(summary_path)
    finals = _read_json(final_path)
    final_by_id = {str(row["workspace_id"]): row for row in finals}

    criteria_sha256 = summary.get("criteria_sha256")
    protocol_fingerprint = summary.get("protocol_fingerprint")
    batches = sorted(
        path
        for path in source_dir.glob("batch_*.json")
        if path.stem.split("_")[1].isdigit()
    )
    if not batches:
        raise SystemExit(f"no source batches under {source_dir}")

    # Deterministic timestamp: the moment the reconciled decision file was
    # written (the export is a view of those bytes, not a new act).
    exported_at = datetime.fromtimestamp(
        final_path.stat().st_mtime, UTC
    ).isoformat()

    provenance = {
        "kind": "DERIVED_EXPORT",
        "decision_status": DECISION_STATUS,
        "human_confirmation": HUMAN_CONFIRMATION,
        "source_batches": str(SOURCE_DIR / "batch_NNN.json"),
        "source_decisions": str(SOURCE_DIR / "decisions"),
        "source_final_decisions": "literature/screening/final_decisions.json",
        "criteria_sha256": criteria_sha256,
        "protocol_fingerprint": protocol_fingerprint,
        "artifact_registry": None,
        "accepted_parent_artifact": False,
        "note": DEV_NOTE,
    }

    bundle = _criteria_bundle(protocol)
    outputs: list[tuple[Path, Any]] = []
    manifest_rows: list[dict[str, Any]] = []
    total_papers = 0

    for index, batch_path in enumerate(batches, start=1):
        source_batch = _read_json(batch_path)
        records = source_batch.get("records") or []
        papers = [_paper(record) for record in records]
        decisions = []
        for record in records:
            record_id = str(record["screening_id"])
            final = final_by_id.get(record_id)
            if final is None:
                raise SystemExit(
                    f"{batch_path.name}: {record_id} has no final decision"
                )
            decisions.append(_decision(record_id, final))
        if len(papers) != len(decisions):
            raise SystemExit(f"{batch_path.name}: paper/decision count mismatch")

        batch_index = index
        batch_doc = {
            "batch_index": batch_index,
            "total_batches": len(batches),
            "batch_size": len(papers),
            "status": "DONE",
            "protocol": bundle,
            "papers": papers,
            "derived_export": provenance,
        }
        decisions_doc = {
            "batch": batch_index,
            "decisions": decisions,
            "reviewed_by": "v03-canonical-export (agent; derived)",
            "timestamp": exported_at,
            "derived_export": provenance,
        }
        out_dir = workspace / "literature" / "screening"
        outputs.append((out_dir / f"batch_{batch_index:03d}.json", batch_doc))
        outputs.append(
            (out_dir / f"batch_{batch_index:03d}_decisions.json", decisions_doc)
        )
        manifest_rows.append(
            {
                "batch_index": batch_index,
                "file": f"batch_{batch_index:03d}.json",
                "decisions_file": f"batch_{batch_index:03d}_decisions.json",
                "paper_count": len(papers),
                "status": "DONE",
            }
        )
        total_papers += len(papers)

    if total_papers != len(finals):
        raise SystemExit(
            f"batch coverage {total_papers} != final decisions {len(finals)}"
        )

    manifest = {
        "screening_run_id": summary.get("session", "v03-calibration-export"),
        "total_papers": total_papers,
        "batch_size": max(row["paper_count"] for row in manifest_rows),
        "total_batches": len(manifest_rows),
        "batches": manifest_rows,
        "derived_export": provenance,
    }
    outputs.insert(0, (workspace / "literature" / "screening" / "MANIFEST.json", manifest))
    return manifest, outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=DEFAULT_WORKSPACE,
        help="workspace root (default: the directory containing _drivers/)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite canonical batch files that already exist",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report the plan without writing anything",
    )
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    manifest, outputs = build(workspace)
    existing = [path for path, _ in outputs if path.exists()]
    if existing and not args.force:
        print(
            f"refusing to overwrite {len(existing)} existing canonical file(s); "
            "re-run with --force",
            file=sys.stderr,
        )
        return 2

    print(
        f"{len(manifest['batches'])} batches / {manifest['total_papers']} papers "
        f"-> {workspace / 'literature' / 'screening'}"
    )
    if args.dry_run:
        print("dry run: nothing written")
        return 0
    for path, payload in outputs:
        _atomic_write(path, payload)
    print(f"wrote {len(outputs)} files (MANIFEST + batches + decisions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
