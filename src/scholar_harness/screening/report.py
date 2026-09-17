from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from .batcher import _screening_dir

try:
    from scholar_agent.calibration import (
        build_checklist_schema,
        build_preflight_calibration,
        checklist_to_decision,
        evaluate_calibration,
    )
    _HAS_CALIBRATION = True
except ImportError:
    _HAS_CALIBRATION = False

logger = logging.getLogger("agent_screen")

def cmd_calibration(workspace_dir: Path, sample_size: int = 20, gold_file: str | None = None) -> None:
    """Generate a 20-paper pre-flight calibration batch from verified.json + gold labels."""
    if not _HAS_CALIBRATION:
        logger.error("scholar-agent-kit calibration module not available. Install scholar-agent-kit.")
        sys.exit(1)

    lit_dir = workspace_dir / "literature"
    verified_path = lit_dir / "verified.json"
    protocol_path = workspace_dir / "protocol.json"

    if not verified_path.exists():
        logger.error("verified.json not found at %s", verified_path)
        sys.exit(1)
    if not protocol_path.exists():
        logger.error("protocol.json not found at %s", protocol_path)
        sys.exit(1)

    raw_verified: list[dict] = json.loads(verified_path.read_text(encoding="utf-8"))
    protocol_data: dict = json.loads(protocol_path.read_text(encoding="utf-8"))

    # Load gold labels if provided; else synthesize from heuristic
    if gold_file and Path(gold_file).exists():
        gold_papers = json.loads(Path(gold_file).read_text(encoding="utf-8"))
        logger.info("Loaded %d gold-labeled papers from %s", len(gold_papers), gold_file)
    else:
        logger.info("No gold file provided; synthesizing gold labels via heuristic screening.")
        gold_papers = []
        for p in raw_verified:
            doc = _rebuild_doc(p, fallback_id=p.get("workspace_id", ""))
            hd = evaluate_heuristic_screening(doc, protocol_data)
            gold_papers.append({
                "workspace_id": p.get("workspace_id", doc.workspace_id),
                "title": p.get("title"),
                "year": p.get("year"),
                "abstract": p.get("abstract"),
                "venue": p.get("venue"),
                "doi": (p.get("external_ids") or {}).get("doi") or p.get("doi"),
                "gold_decision": hd.decision,
                "gold_matched_inclusion": hd.matched_inclusion_criteria,
                "gold_violated_exclusion": hd.violated_exclusion_criteria,
            })

    # Clamp sample size
    sample_size = min(sample_size, len(gold_papers))
    if sample_size == 0:
        logger.error("No papers available for calibration.")
        sys.exit(1)

    screening_dir = _screening_dir(workspace_dir)
    cal_batch = build_preflight_calibration(
        gold_papers, protocol_data, sample_size=sample_size
    )
    cal_batch.write(screening_dir)

    logger.info("=" * 60)
    logger.info("CALIBRATION BATCH PREPARED")
    logger.info("  Papers:    %d", len(cal_batch.batch_data["papers"]))
    logger.info("  Batch:     %s", screening_dir / "calibration_batch_000.json")
    logger.info("  Gold:      %s", screening_dir / "calibration_gold.json")
    logger.info("")
    logger.info("NEXT STEP — ask the agent to screen the calibration batch:")
    logger.info("  'Please screen literature/screening/calibration_batch_000.json'")
    logger.info("  Then run:  python agent_screen.py calibrate-eval %s", workspace_dir)
    logger.info("=" * 60)


def cmd_calibrate_eval(workspace_dir: Path) -> None:
    """Evaluate calibration decisions against gold standard and print report."""
    if not _HAS_CALIBRATION:
        logger.error("scholar-agent-kit calibration module not available.")
        sys.exit(1)

    screening_dir = _screening_dir(workspace_dir)
    decisions_path = screening_dir / "calibration_batch_000_decisions.json"
    gold_path = screening_dir / "calibration_gold.json"

    if not decisions_path.exists():
        logger.error("Calibration decisions file not found: %s", decisions_path)
        sys.exit(1)
    if not gold_path.exists():
        logger.error("Gold standard file not found: %s", gold_path)
        sys.exit(1)

    decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
    gold = json.loads(gold_path.read_text(encoding="utf-8"))

    report = evaluate_calibration(decisions, gold.get("papers", []))

    print(report.to_markdown())
    logger.info("=" * 60)
    logger.info("CALIBRATION VERDICT: %s", report.verdict)
    if report.verdict == "FLAG":
        logger.warning("Calibration FAILED. Review reasons above before proceeding with real screening.")
    else:
        logger.info("Calibration PASSED. Proceed with real screening batches.")
    logger.info("=" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

