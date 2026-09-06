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

# Calibration imports from scholar-agent-kit
try:
    from scholar_agent.calibration import (
        build_checklist_schema,
        build_preflight_calibration,
        evaluate_calibration,
    )
    _HAS_CALIBRATION = True
except ImportError:
    _HAS_CALIBRATION = False

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
        "## Checklist Schema",
        "Fill ONE boolean per criterion per paper. Use `true`/`false`.",
        "```json",
        json.dumps([
            {"criterion_id": inc.get("id"), "criterion_type": "inclusion",
             "description": inc.get("criterion", ""),
             "field_name": inc.get("id", "INC-01").lower().replace("-", "_")}
            for inc in inclusions
        ] + [
            {"criterion_id": exc.get("id"), "criterion_type": "exclusion",
             "description": exc.get("criterion", ""),
             "field_name": exc.get("id", "EXC-01").lower().replace("-", "_")}
            for exc in exclusions
        ], indent=2),
        "```",
        "",
        "## Required Output",
        "Write a JSON array (one object per paper, same order). Each object MUST have:",
        "```json",
        json.dumps([{
            "workspace_id": "SCI-XXXXXX",
            **{inc.get("id", "INC-XX").lower().replace("-", "_"): False
               for inc in inclusions},
            **{exc.get("id", "EXC-XX").lower().replace("-", "_"): False
               for exc in exclusions},
            "screening_reasoning": "One or two sentences explaining the decision."
        }], indent=2),
        "```",
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

    # Check if dual-screening and adjudication files are present
    screener2_files = sorted(screening_dir.glob("batch_*_decisions_screener2.json"))
    adj_files = sorted(screening_dir.glob("_adjudication_resolved_group_*.json"))

    if screener2_files and adj_files:
        logger.info(
            "Detected dual-screening mode: %d screener2 batch files and %d adjudication group files found.",
            len(screener2_files), len(adj_files)
        )
        # Load Screener 1 decisions
        s1_map: dict[str, dict] = {}
        for b in manifest["batches"]:
            idx = b["batch_index"]
            decisions_file = screening_dir / f"batch_{idx:03d}_decisions.json"
            if decisions_file.exists():
                try:
                    for r in json.loads(decisions_file.read_text(encoding="utf-8")):
                        s1_map[r["workspace_id"]] = r
                except Exception:
                    pass

        # Load Screener 2 decisions
        s2_map: dict[str, dict] = {}
        for sf in screener2_files:
            try:
                for r in json.loads(sf.read_text(encoding="utf-8")):
                    s2_map[r["workspace_id"]] = r
            except Exception:
                pass

        # Load Adjudication decisions
        adj_map: dict[str, dict] = {}
        for af in adj_files:
            try:
                for r in json.loads(af.read_text(encoding="utf-8")):
                    adj_map[r["workspace_id"]] = r
            except Exception:
                pass

        # Load confirmed include IDs if available
        reconciled_include_file = screening_dir / "_final_reconciled_include.txt"
        confirmed_inc_ids: set[str] = set()
        if reconciled_include_file.exists():
            try:
                confirmed_inc_ids = set(json.loads(reconciled_include_file.read_text(encoding="utf-8")))
            except Exception:
                pass

        # Load provisional caveat IDs if available (Option B)
        caveats_file = screening_dir / "adjudicated_caveats.json"
        caveat_ids: set[str] = set()
        if caveats_file.exists():
            try:
                cav_list = json.loads(caveats_file.read_text(encoding="utf-8"))
                caveat_ids = {c["workspace_id"] for c in cav_list}
            except Exception:
                pass

        # Build reconciled decisions across all verified documents
        for doc in docs:
            wid = doc.workspace_id
            s1_entry = s1_map.get(wid, {})
            s2_entry = s2_map.get(wid, {})
            a_entry = adj_map.get(wid, {})

            is_disputed = (s1_entry.get("decision") != s2_entry.get("decision"))

            if wid in confirmed_inc_ids or (not confirmed_inc_ids and not is_disputed and s1_entry.get("decision") == "INCLUDE") or (not confirmed_inc_ids and is_disputed and a_entry.get("decision") == "INCLUDE"):
                decision = "INCLUDE"
                conf = float(a_entry.get("confidence", 0.90)) if is_disputed else max(float(s1_entry.get("confidence", 0.8)), float(s2_entry.get("confidence", 0.8)))
                matched = a_entry.get("final_codes", ["INC-01", "INC-02"]) if is_disputed else list(set(s1_entry.get("matched_inclusion_criteria", []) + s2_entry.get("matched_inclusion_criteria", [])))
                violated = []
                rqs = list(set(s2_entry.get("relevant_rqs", []) + s1_entry.get("relevant_rqs", []))) or ["RQ1"]
                reason = a_entry.get("adjudication_reasoning") if is_disputed else (s2_entry.get("screening_reasoning") or s1_entry.get("screening_reasoning"))
            elif wid in caveat_ids:
                decision = "INCLUDE"
                conf = float(a_entry.get("confidence", 0.60))
                matched = ["INC-01", "INC-02"]
                violated = a_entry.get("final_codes", ["EXC-06"])
                rqs = ["RQ1"]
                reason = f"PROVISIONAL INCLUSION (Stage 3 Full-Text Verification Required): {a_entry.get('adjudication_reasoning', '')}"
            else:
                decision = "EXCLUDE"
                conf = float(a_entry.get("confidence", 0.80)) if is_disputed else float(s2_entry.get("confidence", 0.8))
                matched = []
                violated = a_entry.get("final_codes", ["EXC-03"]) if is_disputed else (s2_entry.get("violated_exclusion_criteria") or s1_entry.get("violated_exclusion_criteria") or ["EXC-03"])
                rqs = []
                reason = a_entry.get("adjudication_reasoning") if is_disputed else (s2_entry.get("screening_reasoning") or s1_entry.get("screening_reasoning"))

            all_decisions.append(
                ScreeningDecision(
                    workspace_id=wid,
                    decision=decision,
                    confidence=conf,
                    matched_inclusion_criteria=matched,
                    violated_exclusion_criteria=violated,
                    relevant_rqs=rqs,
                    screening_reasoning=str(reason or "Screened in dual consensus."),
                    document_title=doc.title,
                    doi=doc.external_ids.doi if doc.external_ids else None,
                )
            )

        logger.info(
            "Dual-screening reconciliation generated %d decisions (%d INCLUDE, %d EXCLUDE).",
            len(all_decisions),
            sum(1 for d in all_decisions if d.decision == "INCLUDE"),
            sum(1 for d in all_decisions if d.decision == "EXCLUDE"),
        )
    else:
        for b in manifest["batches"]:
            idx = b["batch_index"]
            decisions_file = screening_dir / f"batch_{idx:03d}_decisions.json"

            if not decisions_file.exists():
                missing_batches.append(idx)
                logger.warning("Batch %d: decision file missing — using heuristic fallback.", idx)
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

                # Support new checklist format (inc_XX/exc_XX booleans)
                # and legacy format (decision + confidence + criteria lists)
                has_checklist = any(k.startswith("inc_") or k.startswith("exc_") for k in entry)
                if has_checklist and _HAS_CALIBRATION:
                    # Deterministic derivation from boolean checklist
                    schema = build_checklist_schema(protocol_data)
                    sd = checklist_to_decision(
                        workspace_id=wsid,
                        checklist=entry,
                        schema=schema,
                        document_title=doc.title if doc else entry.get("title", ""),
                        doi=(doc.external_ids.doi if doc else None) or entry.get("doi"),
                    )
                    all_decisions.append(sd)
                else:
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

    # Look for raw provenance manifest to get exact total_identified and duplicates_removed
    manifest_raw = lit_dir / "raw" / "provenance_manifest.json"
    total_identified = len(docs)
    duplicates_removed = 0
    if manifest_raw.exists():
        try:
            m = json.loads(manifest_raw.read_text(encoding="utf-8"))
            total_identified = m.get("total_raw_harvested", len(docs))
            duplicates_removed = max(0, total_identified - len(docs))
        except Exception:
            pass

    # Partition
    inc_docs, exc_docs, conflicts, report = partition_screening_results(
        docs, all_decisions,
        total_identified=total_identified,
        duplicates_removed=duplicates_removed,
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
    (lit_dir / "prisma_report.json").write_text(
        json.dumps(asdict(report), indent=2), encoding="utf-8"
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
# CALIBRATION
# ---------------------------------------------------------------------------

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

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Agent-in-the-loop PRISMA screening.\n"
            "The harness agent IS the LLM — no external API required.\n\n"
            "Workflow:\n"
            "  1. python agent_screen.py calibration <workspace>  (pre-flight bias check)\n"
            "  2. python agent_screen.py prepare <workspace>\n"
            "  3. Ask the agent: 'screen all batches in literature/screening/'\n"
            "  4. python agent_screen.py collect <workspace>"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # calibration
    p_cal = sub.add_parser("calibration", help="Generate a 20-paper pre-flight calibration batch.")
    p_cal.add_argument("workspace", help="Path to workspace directory")
    p_cal.add_argument("--sample-size", "-n", type=int, default=20)
    p_cal.add_argument("--gold-file", help="Path to gold-labeled JSON (optional; uses heuristic if absent)")

    # calibrate-eval
    p_ceval = sub.add_parser("calibrate-eval", help="Evaluate calibration decisions against gold standard.")
    p_ceval.add_argument("workspace", help="Path to workspace directory")

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

    if args.command == "calibration":
        cmd_calibration(workspace_dir, sample_size=args.sample_size, gold_file=args.gold_file)
    elif args.command == "calibrate-eval":
        cmd_calibrate_eval(workspace_dir)
    elif args.command == "prepare":
        cmd_prepare(workspace_dir, batch_size=args.batch_size, force=args.force)
    elif args.command == "status":
        cmd_status(workspace_dir)
    elif args.command == "collect":
        cmd_collect(workspace_dir)


if __name__ == "__main__":
    main()
