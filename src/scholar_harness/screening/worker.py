"""Deterministic screening-recommendation worker (AG-04).

One worker, one backend: a local deterministic CLI worker. It reads the
assigned immutable batch file (``literature/screening/batch_NNN.json``) plus
verified source material (``literature/verified.json``) and writes draft
recommendation rows ONLY to
``literature/screening/recommendations/batch_NNN_recommendation.json``.
Any other destination refuses with a typed error.

The worker makes NO scientific judgments: each row preserves the study
identifier, criterion references, and source locators, with the decision
carried as explicitly pending review (``PENDING_REVIEW``). Reasons are never
invented (``reasons`` is empty by construction) and uncertainty is recorded
as unreviewed. Worker failure, a missing batch, missing material, or invalid
input produces an explicit typed recoverable error (:class:`WorkerRefused`)
and publishes nothing.

The recommendation file records the worker method/backend plus the parent
batch binding (workspace/run/batch/protocol/corpus) so the review layer can
re-derive the exact scope without trusting worker claims.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scholar_harness.screening.integrity import check_exact_coverage

#: Sidecar identity for one worker recommendation file.
RECOMMENDATION_SCHEMA = "harness-screening-recommendation-v1"

#: The single supported worker method/backend (packet section 2).
WORKER_METHOD = "DETERMINISTIC_CLI"
WORKER_BACKEND = "local-deterministic"

#: Decision carried by every worker row: explicitly pending researcher review.
#: Deliberately NOT one of the AG-02 terminal values and NOT MAYBE/CONFLICT:
#: a pending row can never be finalized without researcher resolution.
PENDING_DECISION = "PENDING_REVIEW"

#: Uncertainty vocabulary for unreviewed worker rows.
UNREVIEWED_UNCERTAINTY = "UNREVIEWED — researcher resolution required"

#: Initial recommendation revision; operator overrides burn new revisions
#: (AG-03B ``supersede``), never rewrites.
INITIAL_REVISION = 1

# --- typed recoverable codes (worker layer) -------------------------------- #
WORKER_BATCH_MISSING = "WORKER_BATCH_MISSING"
WORKER_INVALID_BATCH = "WORKER_INVALID_BATCH"
WORKER_DESTINATION_REFUSED = "WORKER_DESTINATION_REFUSED"
WORKER_PARENT_UNRESOLVED = "WORKER_PARENT_UNRESOLVED"


class WorkerRefused(RuntimeError):
    """Typed recoverable refusal from the recommendation worker.

    Mirrors the ``ScreeningIntegrityRefused``/``AuthorityRefused`` shape
    (stable ``code``, human ``message``, machine-readable ``details``) so
    callers and tests can branch on it. Nothing is published when raised.
    """

    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.details: dict[str, Any] = dict(details)

    def as_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def recommendations_dir(workspace_dir: Path) -> Path:
    """The worker inbox: the ONLY directory the worker may write."""
    return (
        Path(workspace_dir).resolve() / "literature" / "screening" / "recommendations"
    )


def recommendation_path(workspace_dir: Path, batch_index: int) -> Path:
    """Canonical destination for one batch recommendation file."""
    return (
        recommendations_dir(workspace_dir)
        / f"batch_{batch_index:03d}_recommendation.json"
    )


def _batch_file(workspace_dir: Path, batch_index: int) -> Path:
    return (
        Path(workspace_dir).resolve()
        / "literature"
        / "screening"
        / f"batch_{batch_index:03d}.json"
    )


def _resolve_batch_env(
    workspace_dir: Path, batch_data: dict[str, Any]
) -> dict[str, Any]:
    """Resolve the accepted parent batch envelope from the registry.

    Raises :class:`WorkerRefused` (``WORKER_PARENT_UNRESOLVED``) when the
    batch handoff carries no registered parent: the worker never invents
    parent hashes.
    """
    ws = Path(workspace_dir).resolve()
    artifact_id = batch_data.get("artifact_id")
    if not artifact_id:
        raise WorkerRefused(
            WORKER_PARENT_UNRESOLVED,
            "batch handoff carries no parent artifact id; refusing to invent parents",
            batch_index=batch_data.get("batch_index"),
        )
    registry_path = ws / "audit" / "artifact_registry.json"
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        entry = registry.get("artifacts", {}).get(artifact_id)
        batch_env = json.loads((ws / entry["path"]).read_text(encoding="utf-8"))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise WorkerRefused(
            WORKER_PARENT_UNRESOLVED,
            f"cannot resolve accepted parent batch {artifact_id!r} ({exc}); "
            "refusing to invent parents",
            batch_artifact_id=artifact_id,
        ) from exc
    return batch_env


def run_recommend(
    workspace_dir: Path,
    batch_index: int,
    *,
    output_path: Path | None = None,
    produced_at: str | None = None,
) -> Path:
    """Produce the draft recommendation file for one assigned batch.

    Reads the immutable batch file plus verified material, validates both,
    and writes the recommendation payload to the canonical recommendations
    location. ``output_path``, when given, must equal the canonical location
    or the run refuses with ``WORKER_DESTINATION_REFUSED`` — the worker
    cannot write publisher state (approval, policy, registry, audit, final
    outputs) or any other destination.

    On any refusal nothing is published: validation completes before the
    single terminal write.
    """
    ws = Path(workspace_dir).resolve()
    expected = recommendation_path(ws, batch_index)
    if output_path is not None and Path(output_path).resolve() != expected.resolve():
        raise WorkerRefused(
            WORKER_DESTINATION_REFUSED,
            f"worker writes ONLY to {expected}; refusing {output_path}",
            expected=str(expected),
            requested=str(output_path),
        )

    batch_file = _batch_file(ws, batch_index)
    if not batch_file.is_file():
        raise WorkerRefused(
            WORKER_BATCH_MISSING,
            f"assigned batch file {batch_file.name} is absent; "
            "no backend material to recommend from",
            batch_index=batch_index,
            batch_file=str(batch_file),
        )
    try:
        batch_data = json.loads(batch_file.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise WorkerRefused(
            WORKER_INVALID_BATCH,
            f"assigned batch file {batch_file.name} is not valid JSON ({exc})",
            batch_index=batch_index,
        ) from exc
    if not isinstance(batch_data, dict):
        raise WorkerRefused(
            WORKER_INVALID_BATCH,
            f"assigned batch file {batch_file.name} is not a JSON object",
            batch_index=batch_index,
        )
    papers = batch_data.get("papers")
    if not isinstance(papers, list) or not papers:
        raise WorkerRefused(
            WORKER_INVALID_BATCH,
            f"assigned batch file {batch_file.name} carries no papers; "
            "nothing to recommend from",
            batch_index=batch_index,
        )
    criteria = (batch_data.get("protocol") or {}).get("screening_criteria") or {}
    inclusions = criteria.get("inclusion", [])
    exclusions = criteria.get("exclusion", [])
    if not isinstance(inclusions, list) or not isinstance(exclusions, list):
        raise WorkerRefused(
            WORKER_INVALID_BATCH,
            f"assigned batch file {batch_file.name} carries malformed "
            "screening criteria; criterion refs cannot be preserved",
            batch_index=batch_index,
        )
    if not inclusions and not exclusions:
        raise WorkerRefused(
            WORKER_INVALID_BATCH,
            f"assigned batch file {batch_file.name} carries no screening "
            "criteria; criterion refs cannot be preserved",
            batch_index=batch_index,
        )
    inclusion_ids = [str(item.get("id")) for item in inclusions if item.get("id")]
    exclusion_ids = [str(item.get("id")) for item in exclusions if item.get("id")]

    verified_path = ws / "literature" / "verified.json"
    if not verified_path.is_file():
        raise WorkerRefused(
            WORKER_PARENT_UNRESOLVED,
            "verified material literature/verified.json is absent; "
            "source locators cannot be preserved",
            batch_index=batch_index,
        )
    try:
        verified_rows = json.loads(verified_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise WorkerRefused(
            WORKER_PARENT_UNRESOLVED,
            f"verified material is not valid JSON ({exc})",
            batch_index=batch_index,
        ) from exc
    verified_by_id: dict[str, dict[str, Any]] = {}
    if isinstance(verified_rows, list):
        for row in verified_rows:
            if isinstance(row, dict) and row.get("workspace_id"):
                verified_by_id[str(row["workspace_id"])] = row

    batch_env = _resolve_batch_env(ws, batch_data)
    try:
        candidates = batch_env.get("data", {}).get("candidates", [])
        candidate_ids = {str(item.get("study_id")) for item in candidates}
        paper_ids = [
            str(paper.get("workspace_id") or paper.get("study_id") or "")
            for paper in papers
            if isinstance(paper, dict)
        ]
    except (AttributeError, TypeError) as exc:
        raise WorkerRefused(
            WORKER_INVALID_BATCH,
            f"parent batch envelope is malformed ({exc})",
            batch_index=batch_index,
        ) from exc
    if set(paper_ids) != candidate_ids:
        raise WorkerRefused(
            WORKER_INVALID_BATCH,
            "assigned batch papers do not match the accepted parent candidate "
            f"set (papers={sorted(set(paper_ids))}, "
            f"candidates={sorted(candidate_ids)})",
            batch_index=batch_index,
        )

    rows: list[dict[str, Any]] = []
    for study_id, paper in zip(paper_ids, papers):
        verified = verified_by_id.get(study_id, {})
        verified_eids = verified.get("external_ids") or {}
        rows.append(
            {
                "study_id": study_id,
                # Explicitly pending: the worker makes no scientific judgment.
                "decision": PENDING_DECISION,
                # Never invented: the worker records no reasons.
                "reasons": [],
                "uncertainty": UNREVIEWED_UNCERTAINTY,
                "criterion_refs": {
                    "inclusion": list(inclusion_ids),
                    "exclusion": list(exclusion_ids),
                },
                "source_locators": {
                    "title": paper.get("title"),
                    "year": paper.get("year"),
                    "venue": paper.get("venue"),
                    "doi": paper.get("doi") or verified_eids.get("doi"),
                    "url": paper.get("url") or verified.get("url"),
                },
            }
        )
    # The recommendation must exactly cover its parent: no silent drops, no
    # invented studies. AG-02 gate reused read-only (integrity, not authority).
    check_exact_coverage(candidate_ids, [{"study_id": row["study_id"]} for row in rows])

    try:
        registry = json.loads(
            (ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
        )
        batch_sha256 = str(
            registry.get("artifacts", {})
            .get(batch_data["artifact_id"], {})
            .get("sha256", "")
        )
    except (OSError, ValueError, KeyError):
        batch_sha256 = ""
    payload = {
        "schema": RECOMMENDATION_SCHEMA,
        "batch_index": batch_index,
        "batch_id": batch_env.get("data", {}).get("batch_id"),
        "batch_artifact_id": batch_data.get("artifact_id"),
        "batch_sha256": batch_sha256,
        "workspace_id": batch_env.get("workspace_id"),
        "run_id": batch_env.get("run_id"),
        "protocol_fingerprint": batch_env.get("protocol_fingerprint"),
        "corpus_fingerprint": batch_env.get("corpus_fingerprint"),
        "recommendation_revision": INITIAL_REVISION,
        "worker": {
            "method": WORKER_METHOD,
            "backend": WORKER_BACKEND,
            "produced_at": produced_at if produced_at is not None else _utcnow_iso(),
        },
        "rows": rows,
    }

    expected.parent.mkdir(parents=True, exist_ok=True)
    expected.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return expected


def cmd_recommend(workspace_dir: Path, batch_index: int) -> None:
    """CLI entry: produce one batch recommendation file and report it."""
    out = run_recommend(Path(workspace_dir), batch_index)
    payload = json.loads(out.read_text(encoding="utf-8"))
    print(f"Wrote worker recommendation: {out}")
    print(
        f"  batch {batch_index}: {len(payload['rows'])} rows, "
        "all PENDING_REVIEW (researcher resolution required)"
    )
