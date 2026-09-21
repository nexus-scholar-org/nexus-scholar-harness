from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from scholar_harness.contracts import AcceptanceContext, accept_artifact
from scholar_harness.contracts.canonical import canonical_fingerprint, deterministic_id
from scholar_harness.contracts.identifiers import IdentifierKind
from scholar_harness.contracts.models import (
    ScreeningBatchData,
    ScreeningBinding,
    ScreeningCandidate,
)
from scholar_protocol.canonical import canonical_fingerprint as protocol_fingerprint
from scholar_protocol.models import ResearchProtocol
from scholar_search.models import Author, Document, ExternalIds

logger = logging.getLogger("agent_screen")


def _harness_commit() -> str:
    explicit = os.environ.get("NEXUS_HARNESS_COMMIT", "").strip()
    if explicit:
        return explicit
    result = subprocess.run(
        ["git", "-C", str(Path(__file__).resolve().parents[3]), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"

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


def _load_decision_payload(path: Path) -> tuple[list[dict], dict[str, str]]:
    """Load decisions and preserve wrapper provenance for Contract v1 migration."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        decisions = payload.get("decisions")
        if not isinstance(decisions, list):
            raise ValueError(f"{path.name}: 'decisions' key must be a list")
        return decisions, {
            "reviewed_by": str(payload.get("reviewed_by") or "agent-unknown"),
            "timestamp": str(payload.get("timestamp") or ""),
        }
    if isinstance(payload, list):
        timestamp = datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()
        return payload, {"reviewed_by": "agent-legacy", "timestamp": timestamp}
    raise ValueError(
        f"{path.name}: expected a JSON list or wrapper object, got {type(payload).__name__}"
    )


# ---------------------------------------------------------------------------
# PREPARE
# ---------------------------------------------------------------------------

def cmd_prepare(workspace_dir: Path, batch_size: int = 20, force: bool = False) -> None:
    """Create generation-bound screening batches from the accepted corpus."""
    protocol_path = workspace_dir / "protocol.json"
    registry_path = workspace_dir / "audit" / "artifact_registry.json"

    if not protocol_path.exists():
        logger.error("protocol.json not found at %s", protocol_path)
        sys.exit(1)
    if not registry_path.exists():
        logger.error("No artifact registry found. Accept a corpus snapshot first.")
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

    protocol_data: dict = json.loads(protocol_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    corpus_items = [
        (artifact_id, entry)
        for artifact_id, entry in registry.get("artifacts", {}).items()
        if entry.get("artifact_type") == "corpus_snapshot"
    ]
    if not corpus_items:
        logger.error("No accepted corpus snapshot found in the artifact registry.")
        sys.exit(1)
    corpus_id, corpus_entry = max(
        corpus_items, key=lambda item: item[1].get("accepted_at", "")
    )
    corpus_env = json.loads(
        (workspace_dir / corpus_entry["path"]).read_text(encoding="utf-8")
    )
    actual_protocol_fingerprint = protocol_fingerprint(
        ResearchProtocol.model_validate(protocol_data)
    )
    if actual_protocol_fingerprint != corpus_env["protocol_fingerprint"]:
        logger.error("protocol.json does not match the accepted corpus generation.")
        sys.exit(1)

    protocol_summary = {
        "title": (protocol_data.get("metadata") or {}).get("title", "Research Protocol"),
        "research_questions": protocol_data.get("research_questions", []),
        "screening_criteria": protocol_data.get("screening_criteria", {}),
    }

    candidates = [
        ScreeningCandidate(
            study_id=study["study_id"],
            title=study["title"],
            abstract=None,
        )
        for study in corpus_env["data"]["studies"]
    ]
    chunks = [
        candidates[i : i + batch_size]
        for i in range(0, len(candidates), batch_size)
    ]
    total_batches = len(chunks)
    renderer_version = "scholar-protocol-criteria-v1"
    dedup_hash = canonical_fingerprint(
        {"identity_algorithm_version": corpus_env["data"]["identity_algorithm_version"]}
    )
    run_id = deterministic_id(
        IdentifierKind.RUN,
        corpus_env["workspace_id"],
        {
            "protocol_fingerprint": actual_protocol_fingerprint,
            "corpus_fingerprint": corpus_env["corpus_fingerprint"],
            "renderer_version": renderer_version,
            "dedup_configuration_hash": dedup_hash,
        },
    )
    binding = ScreeningBinding(
        screening_run_id=run_id,
        protocol_fingerprint=actual_protocol_fingerprint,
        corpus_fingerprint=corpus_env["corpus_fingerprint"],
        criteria_renderer_version=renderer_version,
        dedup_configuration_hash=dedup_hash,
        preparation_run_id=run_id,
    )

    logger.info(
        "Preparing %d batches of up to %d papers from %d verified documents.",
        total_batches, batch_size, len(candidates),
    )

    for idx, chunk in enumerate(chunks, start=1):
        batch_id = deterministic_id(
            IdentifierKind.ARTIFACT,
            corpus_env["workspace_id"],
            {"kind": "screening-batch", "run_id": run_id, "batch_index": idx},
        ).replace("ART-", "batch-", 1)
        data = ScreeningBatchData(
            binding=binding,
            batch_id=batch_id,
            batch_index=idx,
            candidates=chunk,
        )
        artifact_id = deterministic_id(
            IdentifierKind.ARTIFACT,
            corpus_env["workspace_id"],
            {"kind": "screening-batch-artifact", "batch_id": batch_id},
        )
        existing_entry = registry.get("artifacts", {}).get(artifact_id)
        created_at = datetime.now(UTC).isoformat()
        if existing_entry:
            existing_payload = json.loads(
                (workspace_dir / existing_entry["path"]).read_text(encoding="utf-8")
            )
            created_at = existing_payload["created_at"]
        envelope = {
            "schema_version": "1.0.0",
            "artifact_type": "screening_batch",
            "artifact_id": artifact_id,
            "created_at": created_at,
            "producer": {
                "package": "nexus-scholar-harness",
                "version": "1.0.0",
                "commit": _harness_commit(),
            },
            "workspace_id": corpus_env["workspace_id"],
            "run_id": run_id,
            "protocol_fingerprint": actual_protocol_fingerprint,
            "corpus_fingerprint": corpus_env["corpus_fingerprint"],
            "inputs": [{"artifact_id": corpus_id, "sha256": corpus_entry["sha256"]}],
            "data": data.model_dump(mode="json"),
        }
        result = accept_artifact(
            workspace_dir,
            envelope,
            expected=AcceptanceContext(
                workspace_id=corpus_env["workspace_id"],
                protocol_fingerprint=actual_protocol_fingerprint,
                corpus_fingerprint=corpus_env["corpus_fingerprint"],
            ),
            actor="agent_screen.prepare",
        )
        if not result.accepted:
            logger.error("Failed to accept batch %d: %s", idx, result.issues)
            sys.exit(1)

        papers_for_batch = [
            {
                "workspace_id": candidate.study_id,
                "title": candidate.title,
                "year": None,
                "abstract": candidate.abstract or "No abstract available.",
                "venue": None,
                "doi": None,
            }
            for candidate in chunk
        ]

        batch_file = screening_dir / f"batch_{idx:03d}.json"
        batch_data = {
            "batch_index": idx,
            "total_batches": total_batches,
            "batch_size": len(papers_for_batch),
            "status": "PENDING",
            "artifact_id": artifact_id,
            "binding": binding.model_dump(mode="json"),
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
        "screening_run_id": run_id,
        "total_papers": len(candidates),
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

