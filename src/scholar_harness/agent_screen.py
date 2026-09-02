#!/usr/bin/env python3
"""
agent_screen.py — Agent-in-the-loop PRISMA screening for the scholar-harness.

The harness itself is the LLM — no external API key required.
This script implements a file-based handoff protocol between the pipeline
and the agent (which reads batch files and writes decision files).

WORKFLOW
--------
Step 1 — PREPARE (run once):
    python agent_screen.py prepare <workspace_dir>

    Reads literature/verified.json + protocol.json.
    Writes literature/screening/batch_NNN.json for each group of 20 papers.
    Each batch file contains the full protocol context + papers.

Step 2 — AGENT SCREENS (the harness/agent does this):
    The agent reads each batch_NNN.json, evaluates papers, and writes
    batch_NNN_decisions.json in the same directory.

Step 3 — COLLECT (run after all decision files are written):
    python agent_screen.py collect <workspace_dir>

    Reads all batch_NNN_decisions.json files.
    Writes included.json, excluded.json, conflicts.json, prisma_screening_report.md.

Step 4 — STATUS (check progress at any time):
    python agent_screen.py status <workspace_dir>

BATCH FILE FORMAT (batch_NNN.json)
-----------------------------------
{
  "batch_index": 1,
  "total_batches": 8,
  "batch_size": 20,
  "status": "PENDING",          // PENDING | DONE
  "protocol": {
    "title": "...",
    "research_questions": [...],
    "screening_criteria": {
      "inclusion": [...],
      "exclusion": [...]
    }
  },
  "papers": [
    {
      "workspace_id": "SCI-000001",
      "title": "...",
      "year": 2023,
      "abstract": "...",
      "venue": "..."
    }
  ],
  "agent_instructions": "..."   // full plain-text prompt for the agent
}

DECISION FILE FORMAT (batch_NNN_decisions.json)
------------------------------------------------
[
  {
    "workspace_id": "SCI-000001",
    "decision": "INCLUDE",
    "confidence": 0.90,
    "matched_inclusion_criteria": ["INC-01", "INC-02"],
    "violated_exclusion_criteria": [],
    "relevant_rqs": ["RQ1"],
    "screening_reasoning": "Paper directly evaluates multispectral weed detection..."
  }
]
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path

# Allow running from repo root without install
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools/scholar-search-kit/src"))

from scholar_search.models import Document, ExternalIds, Author
from scholar_search.screening import (
    ScreeningDecision,
    evaluate_heuristic_screening,
    partition_screening_results,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("agent_screen")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rebuild_doc(raw: dict, fallback_id: str) -> Document:
    """Reconstruct a Document dataclass from a JSON dict (from verified.json)."""
    eids = raw.get("external_ids") or {}
    authors_raw = raw.get("authors") or []
    authors = [
        Author(family_name=a.get("family_name", ""), given_name=a.get("given_name"))
        for a in authors_raw
    ]
    return Document(
        title=raw.get("title") or "Untitled",
        year=raw.get("year"),
        provider=raw.get("provider", "unknown"),
        provider_id=raw.get("provider_id", ""),
        external_ids=ExternalIds(
            doi=eids.get("doi"),
            arxiv_id=eids.get("arxiv_id"),
            pubmed_id=eids.get("pubmed_id"),
            openalex_id=eids.get("openalex_id"),
            s2_id=eids.get("s2_id"),
        ),
        abstract=raw.get("abstract"),
        authors=authors,
        venue=raw.get("venue"),
        url=raw.get("url"),
        workspace_id=raw.get("workspace_id") or fallback_id,
        citations_count=raw.get("citations_count"),
        references_count=raw.get("references_count"),
    )


def _build_agent_instructions(
    protocol: dict,
    papers: list[dict],
    batch_index: int,
    total_batches: int,
) -> str:
    """Build the plain-text prompt the agent will read to screen the batch."""
    rqs = protocol.get("research_questions", [])
    criteria = protocol.get("screening_criteria", {})
    inclusions = criteria.get("inclusion", [])
    exclusions = criteria.get("exclusion", [])

    lines = [
        f"# PRISMA 2020 Screening — Batch {batch_index}/{total_batches}",
        "",
        "You are performing a systematic literature review screening step.",
        "Evaluate EACH paper below against the protocol criteria.",
        "",
        "## Research Questions",
    ]
    for rq in rqs:
        lines.append(f"- **{rq.get('id', 'RQ')}**: {rq.get('text', '')}")

    lines += ["", "## Inclusion Criteria (must match to INCLUDE)"]
    for inc in inclusions:
        lines.append(f"- **{inc.get('id')}**: {inc.get('criterion', '')}")

    lines += ["", "## Exclusion Criteria (any match → EXCLUDE)"]
    for exc in exclusions:
        code = exc.get("id")
        cat = exc.get("reason_category", "")
        lines.append(f"- **{code}** ({cat}): {exc.get('criterion', '')}")

    lines += [
        "",
        "## Papers to Screen",
        "```json",
        json.dumps(papers, indent=2, ensure_ascii=False),
        "```",
        "",
        "## Required Output",
        "Write a JSON array (one object per paper, same order) to the decision file.",
        "Each object MUST have these exact fields:",
        "```json",
        json.dumps([{
            "workspace_id": "SCI-XXXXXX",
            "decision": "INCLUDE or EXCLUDE",
            "confidence": 0.0,
            "matched_inclusion_criteria": ["INC-01"],
            "violated_exclusion_criteria": [],
            "relevant_rqs": ["RQ1"],
            "screening_reasoning": "One or two sentences explaining the decision."
        }], indent=2),
        "```",
        "",
        f"Write your response to: `literature/screening/batch_{batch_index:03d}_decisions.json`",
    ]
    return "\n".join(lines)


def _screening_dir(workspace_dir: Path) -> Path:
    d = workspace_dir / "literature" / "screening"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# PREPARE
# ---------------------------------------------------------------------------

def cmd_prepare(workspace_dir: Path, batch_size: int = 20, force: bool = False) -> None:
    """Chunk verified.json into batch files ready for the agent to screen."""
    lit_dir = workspace_dir / "literature"
    verified_path = lit_dir / "verified.json"
    protocol_path = workspace_dir / "protocol.json"

    if not verified_path.exists():
        logger.error("verified.json not found at %s", verified_path)
        sys.exit(1)
    if not protocol_path.exists():
        logger.error("protocol.json not found at %s", protocol_path)
        sys.exit(1)

    screening_dir = _screening_dir(workspace_dir)

    # Check if batches already exist
    existing = list(screening_dir.glob("batch_*.json"))
    existing_batches = [f for f in existing if "_decisions" not in f.name]
    if existing_batches and not force:
        logger.warning(
            "%d batch file(s) already exist in %s.\n"
            "  Run with --force to overwrite, or use 'status' to check progress.",
            len(existing_batches), screening_dir,
        )
        sys.exit(0)

    raw_verified: list[dict] = json.loads(verified_path.read_text(encoding="utf-8"))
    protocol_data: dict = json.loads(protocol_path.read_text(encoding="utf-8"))

    protocol_summary = {
        "title": (protocol_data.get("metadata") or {}).get("title", "Research Protocol"),
        "research_questions": protocol_data.get("research_questions", []),
        "screening_criteria": protocol_data.get("screening_criteria", {}),
    }

    # Chunk into batches
    chunks = [
        raw_verified[i : i + batch_size]
        for i in range(0, len(raw_verified), batch_size)
    ]
    total_batches = len(chunks)

    logger.info(
        "Preparing %d batches of up to %d papers from %d verified documents.",
        total_batches, batch_size, len(raw_verified),
    )

    for idx, chunk in enumerate(chunks, start=1):
        # Build the lightweight paper list for the batch file
        papers_for_batch = [
            {
                "workspace_id": p.get("workspace_id") or f"SCI-{((idx-1)*batch_size + i + 1):06d}",
                "title": p.get("title", "Untitled"),
                "year": p.get("year"),
                "abstract": p.get("abstract") or "No abstract available.",
                "venue": p.get("venue"),
                "doi": (p.get("external_ids") or {}).get("doi") or p.get("doi"),
            }
            for i, p in enumerate(chunk)
        ]

        batch_file = screening_dir / f"batch_{idx:03d}.json"
        batch_data = {
            "batch_index": idx,
            "total_batches": total_batches,
            "batch_size": len(papers_for_batch),
            "status": "PENDING",
            "protocol": protocol_summary,
            "papers": papers_for_batch,
            "agent_instructions": _build_agent_instructions(
                protocol_summary, papers_for_batch, idx, total_batches
            ),
        }
        batch_file.write_text(
            json.dumps(batch_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.info("  Written: %s (%d papers)", batch_file.name, len(papers_for_batch))

    # Write a manifest
    manifest = {
        "total_papers": len(raw_verified),
        "batch_size": batch_size,
        "total_batches": total_batches,
        "batches": [
            {
                "batch_index": i + 1,
                "file": f"batch_{i+1:03d}.json",
                "decisions_file": f"batch_{i+1:03d}_decisions.json",
                "paper_count": len(chunks[i]),
                "status": "PENDING",
            }
            for i in range(total_batches)
        ],
    }
    (screening_dir / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    logger.info("")
    logger.info("=" * 60)
    logger.info("PREPARED %d batch files in:", total_batches)
    logger.info("  %s", screening_dir)
    logger.info("")
    logger.info("NEXT STEP — ask the agent to screen the batches:")
    logger.info("  'Please screen all batches in literature/screening/'")
    logger.info("  The agent will read each batch_NNN.json and write")
    logger.info("  batch_NNN_decisions.json in the same directory.")
    logger.info("")
    logger.info("When done, run:")
    logger.info("  python agent_screen.py collect %s", workspace_dir)
    logger.info("=" * 60)


# ---------------------------------------------------------------------------
# STATUS
# ---------------------------------------------------------------------------

def cmd_status(workspace_dir: Path) -> None:
    """Show which batches are pending and which have decisions."""
    screening_dir = _screening_dir(workspace_dir)
    manifest_path = screening_dir / "MANIFEST.json"
    if not manifest_path.exists():
        logger.error("No manifest found. Run 'prepare' first.")
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    total = manifest["total_batches"]
    done = 0
    pending = []

    print(f"\nScreening status for: {workspace_dir.name}")
    print(f"{'Batch':<8} {'Papers':<8} {'Status':<12} {'Decision file'}")
    print("-" * 55)
    for b in manifest["batches"]:
        idx = b["batch_index"]
        decisions_file = screening_dir / f"batch_{idx:03d}_decisions.json"
        if decisions_file.exists():
            try:
                decisions = json.loads(decisions_file.read_text(encoding="utf-8"))
                inc = sum(1 for d in decisions if d.get("decision") == "INCLUDE")
                exc = sum(1 for d in decisions if d.get("decision") == "EXCLUDE")
                status = f"DONE ({inc}I/{exc}E)"
                done += 1
            except Exception:
                status = "DONE (parse error)"
                done += 1
        else:
            status = "PENDING"
            pending.append(idx)
        print(f"  {idx:<6} {b['paper_count']:<8} {status:<12} {decisions_file.name}")

    print()
    print(f"Progress: {done}/{total} batches complete.")
    if pending:
        print(f"Pending batches: {pending}")
        print(f"\nAsk the agent to screen: literature/screening/batch_{pending[0]:03d}.json")
    else:
        print("All batches done! Run: python agent_screen.py collect <workspace>")


# ---------------------------------------------------------------------------
# COLLECT
# ---------------------------------------------------------------------------

def cmd_collect(workspace_dir: Path) -> None:
    """Assemble all decision files into the final screening outputs."""
    screening_dir = _screening_dir(workspace_dir)
    lit_dir = workspace_dir / "literature"
    manifest_path = screening_dir / "MANIFEST.json"
    verified_path = lit_dir / "verified.json"

    if not manifest_path.exists():
        logger.error("No manifest found. Run 'prepare' first.")
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw_verified: list[dict] = json.loads(verified_path.read_text(encoding="utf-8"))

    # Rebuild Document objects
    docs: list[Document] = []
    for i, raw in enumerate(raw_verified):
        docs.append(_rebuild_doc(raw, fallback_id=raw.get("workspace_id") or f"SCI-{i+1:06d}"))

    # Collect all decisions
    all_decisions: list[ScreeningDecision] = []
    missing_batches: list[int] = []
    fallback_count = 0

    protocol_path = workspace_dir / "protocol.json"
    protocol_data = json.loads(protocol_path.read_text(encoding="utf-8"))

    # Build doc lookup by workspace_id
    doc_by_wsid: dict[str, Document] = {d.workspace_id: d for d in docs if d.workspace_id}

    for b in manifest["batches"]:
        idx = b["batch_index"]
        decisions_file = screening_dir / f"batch_{idx:03d}_decisions.json"

        if not decisions_file.exists():
            missing_batches.append(idx)
            logger.warning("Batch %d: decision file missing — using heuristic fallback.", idx)
            # Fallback: load the batch file and heuristic-screen those papers
            batch_file = screening_dir / f"batch_{idx:03d}.json"
            if batch_file.exists():
                batch_data = json.loads(batch_file.read_text(encoding="utf-8"))
                for p in batch_data.get("papers", []):
                    wsid = p.get("workspace_id", "")
                    doc = doc_by_wsid.get(wsid)
                    if doc:
                        all_decisions.append(evaluate_heuristic_screening(doc, protocol_data))
                        fallback_count += 1
            continue

        try:
            raw_decisions: list[dict] = json.loads(decisions_file.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.error("Batch %d: failed to parse decisions file (%s).", idx, exc)
            missing_batches.append(idx)
            continue

        for entry in raw_decisions:
            wsid = str(entry.get("workspace_id", ""))
            doc = doc_by_wsid.get(wsid)

            raw_dec = str(entry.get("decision", "INCLUDE")).upper()
            decision = "INCLUDE" if raw_dec == "INCLUDE" else "EXCLUDE"
            try:
                confidence = float(entry.get("confidence", 0.80))
            except (TypeError, ValueError):
                confidence = 0.80

            all_decisions.append(
                ScreeningDecision(
                    workspace_id=wsid,
                    decision=decision,
                    confidence=confidence,
                    matched_inclusion_criteria=list(entry.get("matched_inclusion_criteria") or []),
                    violated_exclusion_criteria=list(entry.get("violated_exclusion_criteria") or []),
                    relevant_rqs=list(entry.get("relevant_rqs") or []),
                    screening_reasoning=str(entry.get("screening_reasoning", "Agent screened.")),
                    document_title=doc.title if doc else entry.get("title", ""),
                    doi=doc.external_ids.doi if doc else None,
                )
            )

    if missing_batches:
        logger.warning("%d batch(es) had missing/broken decision files: %s", len(missing_batches), missing_batches)
    if fallback_count:
        logger.warning("%d papers fell back to heuristic screening.", fallback_count)

    # Partition
    inc_docs, exc_docs, conflicts, report = partition_screening_results(
        docs, all_decisions,
        total_identified=len(docs),
        duplicates_removed=0,
    )

    # Write outputs
    (lit_dir / "included.json").write_text(
        json.dumps(inc_docs, indent=2, default=str, ensure_ascii=False), encoding="utf-8"
    )
    (lit_dir / "excluded.json").write_text(
        json.dumps(exc_docs, indent=2, default=str, ensure_ascii=False), encoding="utf-8"
    )
    (lit_dir / "conflicts.json").write_text(
        json.dumps(conflicts, indent=2, default=str, ensure_ascii=False), encoding="utf-8"
    )
    (lit_dir / "prisma_screening_report.md").write_text(
        report.to_markdown(), encoding="utf-8"
    )

    # Update manifest statuses
    for b in manifest["batches"]:
        idx = b["batch_index"]
        decisions_file = screening_dir / f"batch_{idx:03d}_decisions.json"
        b["status"] = "DONE" if decisions_file.exists() else "MISSING"
    (screening_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    inc_with_abs = sum(1 for d in inc_docs if d.get("abstract") and len(d.get("abstract", "")) > 30)
    logger.info("=" * 60)
    logger.info("COLLECTION COMPLETE")
    logger.info("  Included:               %d", len(inc_docs))
    logger.info("  Excluded:               %d", len(exc_docs))
    logger.info("  Conflicts (audit):      %d", len(conflicts))
    logger.info("  Included with abstract: %d/%d", inc_with_abs, len(inc_docs))
    logger.info("  Missing decision files: %d", len(missing_batches))
    logger.info("=" * 60)
    print()
    print(report.to_markdown())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Agent-in-the-loop PRISMA screening.\n"
            "The harness agent IS the LLM — no external API required.\n\n"
            "Workflow:\n"
            "  1. python agent_screen.py prepare <workspace>\n"
            "  2. Ask the agent: 'screen all batches in literature/screening/'\n"
            "  3. python agent_screen.py collect <workspace>"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # prepare
    p_prepare = sub.add_parser("prepare", help="Chunk verified.json into batch files.")
    p_prepare.add_argument("workspace", help="Path to workspace directory")
    p_prepare.add_argument("--batch-size", "-b", type=int, default=20)
    p_prepare.add_argument("--force", action="store_true", help="Overwrite existing batch files")

    # status
    p_status = sub.add_parser("status", help="Show screening progress.")
    p_status.add_argument("workspace", help="Path to workspace directory")

    # collect
    p_collect = sub.add_parser("collect", help="Assemble decision files into final outputs.")
    p_collect.add_argument("workspace", help="Path to workspace directory")

    args = parser.parse_args()
    workspace_dir = Path(args.workspace).resolve()

    if args.command == "prepare":
        cmd_prepare(workspace_dir, batch_size=args.batch_size, force=args.force)
    elif args.command == "status":
        cmd_status(workspace_dir)
    elif args.command == "collect":
        cmd_collect(workspace_dir)


if __name__ == "__main__":
    main()
