from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from scholar_search.models import Author, Document, ExternalIds

logger = logging.getLogger("agent_screen")

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


def _load_decisions(path: Path) -> list[dict]:
    """Load a decisions file tolerating both the §7 wrapper and the raw list.

    The console writes the wrapper `{"batch", "decisions", "reviewed_by",
    "timestamp"}`; agents historically wrote a raw JSON array. Both shapes must
    round-trip through `collect` without any transform of the decision records.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        decisions = payload.get("decisions")
        if not isinstance(decisions, list):
            raise ValueError(f"{path.name}: 'decisions' key must be a list")
        return decisions
    if isinstance(payload, list):
        return payload
    raise ValueError(f"{path.name}: expected a JSON list or wrapper object, got {type(payload).__name__}")


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

