"""Screening decision writer (SPECS §3, §7, §8).

`POST /api/v1/screening/batch/{n}/decisions` writes the canonical
`batch_NNN_decisions.json` in the §7 wrapper shape the agent handoff expects:

    {"batch": n, "decisions": [...], "reviewed_by": "...", "timestamp": "..."}

Dual-compatibility: each decision accepts `study_id` or `workspace_id`, and
`cmd_collect` (agent_screen.py) accepts both the wrapper and the legacy raw
array, so GUI-written and agent-written files stay interchangeable.

All writes are atomic: `<file>.tmp-<uuid>` then `os.replace`, followed by one
append-only audit journal event (SPECS §8).
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, field_validator

from .audit import log_event

router = APIRouter(prefix="/api/v1/screening", tags=["screening"])

_DECISION_CODES = ("INCLUDE", "EXCLUDE")
_CONFIDENCE_WORDS = {"high": 0.9, "medium": 0.7, "low": 0.5}


class Decision(BaseModel):
    model_config = ConfigDict(extra="ignore")

    workspace_id: str | None = None
    study_id: str | None = None
    decision: str
    confidence: float | str = 0.8
    matched_inclusion_criteria: list[str] = []
    violated_exclusion_criteria: list[str] = []
    relevant_rqs: list[str] = []
    screening_reasoning: str = ""

    @field_validator("decision")
    @classmethod
    def _decision_upper(cls, v: str) -> str:
        raw = (v or "").strip().upper()
        if raw not in _DECISION_CODES:
            raise ValueError(f"decision must be INCLUDE or EXCLUDE, got {v!r}")
        return raw

    @property
    def resolved_id(self) -> str:
        return self.workspace_id or self.study_id or ""

    def to_record(self) -> dict[str, Any]:
        confidence = self.confidence
        if isinstance(confidence, str):
            confidence = _CONFIDENCE_WORDS.get(confidence.strip().lower(), 0.8)
        c = float(confidence)
        if not 0 <= c <= 1:
            raise ValueError(f"confidence must be in [0,1], got {confidence!r}")
        return {
            "workspace_id": self.resolved_id,
            "decision": self.decision,
            "confidence": c,
            "matched_inclusion_criteria": list(self.matched_inclusion_criteria),
            "violated_exclusion_criteria": list(self.violated_exclusion_criteria),
            "relevant_rqs": list(self.relevant_rqs),
            "screening_reasoning": self.screening_reasoning
            or f"{self.decision.lower()} during console verification review",
        }


class DecisionsBody(BaseModel):
    model_config = ConfigDict(extra="ignore")

    batch: int | None = None
    decisions: list[Decision]
    reviewed_by: str = "console"
    timestamp: str | None = None


def _batch_file(ws: Path, n: int) -> Path:
    return ws / "literature" / "screening" / f"batch_{n:03d}.json"


def _atomic_write_json(path: Path, payload: Any) -> None:
    tmp = path.with_name(path.name + f".tmp-{uuid.uuid4().hex[:8]}")
    tmp.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    os.replace(tmp, path)


@router.post("/batch/{n}/decisions", status_code=200)
def post_batch_decisions(
    body: DecisionsBody, n: int, request: Request
) -> dict[str, Any]:
    ws: Path = request.app.state.workspace
    batch_path = _batch_file(ws, n)
    if not batch_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"missing file: literature/screening/batch_{n:03d}.json",
        )

    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    known_ids = {str(p.get("workspace_id", "")) for p in batch.get("papers", [])}
    known_ids.discard("")

    if body.batch is not None and body.batch != n:
        raise HTTPException(
            status_code=400,
            detail=f"body batch={body.batch} disagrees with path batch={n}",
        )

    if not body.decisions:
        raise HTTPException(status_code=400, detail="decisions list must not be empty")

    records: list[dict[str, Any]] = []
    unknown: list[str] = []
    for dec in body.decisions:
        try:
            record = dec.to_record()
        except ValueError as exc:
            raise HTTPException(
                status_code=422, detail=f"invalid decision: {exc}"
            ) from exc
        if record["workspace_id"] not in known_ids:
            unknown.append(record["workspace_id"])
        records.append(record)

    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"decisions reference unknown workspace_ids (not in batch {n}): {sorted(set(unknown))}",
        )

    timestamp = body.timestamp or datetime.now(UTC).isoformat()
    payload = {
        "batch": n,
        "decisions": records,
        "reviewed_by": body.reviewed_by,
        "timestamp": timestamp,
    }

    decisions_file = ws / "literature" / "screening" / f"batch_{n:03d}_decisions.json"
    _atomic_write_json(decisions_file, payload)

    inc = sum(1 for r in records if r["decision"] == "INCLUDE")
    exc = len(records) - inc
    log_event(
        workspace=ws,
        action="SCREEN_DECISIONS",
        description=f"Saved {len(records)} screening decisions for batch {n} ({inc} INCLUDE / {exc} EXCLUDE)",
        inputs=[batch_path.name],
        outputs=[decisions_file.name],
        parameters={"batch": n, "reviewed_by": body.reviewed_by},
        metrics={"included": inc, "excluded": exc, "total": len(records)},
    )

    return {
        "batch": n,
        "decisions_written": len(records),
        "decisions_file": decisions_file.name,
    }


# ---------------------------------------------------------------------------
# UI-07 screening presentation shapes (HCM-06 read side; GET only).
#
# The POST decisions route above is untouched: it keeps writing draft
# decision files only. Everything below is a pure read over the workspace
# bound at app state, serving the UI-07 presentation spec §§3-5 shapes:
#
# * GET /ui/batches                        §3(b) screening batches envelope
# * GET /ui/batch/{n}/rows                 §3(b) per-record rows (paginated;
#                                          OQ-P1 row paging is limit/offset)
# * GET /ui/batch/{n}/review               §3(d) recommendation / resolution /
#                                          override / review / deferral
# * GET /ui/batch/{n}/criterion-refs       §3(c) criteria + source locators
# * GET /ui/audit-feed                     §3(f) journey-scoped audit feed
#
# Discipline mirrors console/api/workspace.py's UI-07 section: backend-
# resolved references (R1), caller-minted identities refused with 422 (R2),
# explicit `missing` entries (R4), pure reads that never write/repair/mint
# (R5). Authority primitives are reused, never rewritten:
# screening.integrity (AG-02 coverage/unresolved gates, read-only),
# screening.worker (recommendation layout + pending vocabulary),
# authority.review path conventions (review/approval/deferral sidecars).
# ---------------------------------------------------------------------------


def _ui07_error(
    status_code: int, code: str, message: str, **details: Any
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": details},
    )


def _ui07_refuse_caller_identity(request: Request) -> None:
    hits = sorted(
        str(key)
        for key in request.query_params
        if str(key).lower().replace("-", "").replace("_", "")
        in {
            "workspaceid",
            "registeredworkspaceid",
            "runid",
            "screeningrunid",
            "protocolfingerprint",
            "corpusfingerprint",
            "generationid",
            "artifactid",
            "batchartifactid",
            "batchid",
            "fingerprint",
        }
    )
    if hits:
        raise _ui07_error(
            422,
            "CALLER_IDENTITY_REFUSED",
            "identity comes from the bound workspace, never the browser; "
            f"refusing caller-supplied identity parameter(s): {hits}",
            refused_parameters=hits,
        )


def _ui07_ws(request: Request) -> Path:
    return Path(request.app.state.workspace).resolve()


def _ui07_screening_dir(ws: Path) -> Path:
    return ws / "literature" / "screening"


def _ui07_read_json(path: Path, *, missing_code: str) -> Any:
    """Read canonical JSON: explicit 404 when absent, typed 500 when unparseable."""
    if not path.is_file():
        raise _ui07_error(
            404, missing_code, f"missing file: {path.name}", file=path.name
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - malformed canonical bytes are explicit
        raise _ui07_error(
            500,
            "UNPARSEABLE_JSON",
            f"unparseable JSON: {path.name} ({exc})",
            file=path.name,
        ) from exc


def _ui07_manifest(ws: Path) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Return (manifest, missing-entry): absent/unreadable manifests are explicit."""
    path = _ui07_screening_dir(ws) / "MANIFEST.json"
    if not path.is_file():
        return None, {
            "file": "literature/screening/MANIFEST.json",
            "reason": "NOT_PREPARED",
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise _ui07_error(
            500,
            "UNPARSEABLE_JSON",
            f"unparseable JSON: MANIFEST.json ({exc})",
            file="MANIFEST.json",
        ) from exc
    if not isinstance(payload, dict):
        raise _ui07_error(
            500,
            "UNPARSEABLE_JSON",
            "unparseable JSON: MANIFEST.json (not an object)",
            file="MANIFEST.json",
        )
    return payload, None


def _ui07_row_key(entry: dict[str, Any]) -> str:
    """Canonical row key (AG-02 coverage expression): workspace_id or study_id."""
    return str(entry.get("workspace_id") or entry.get("study_id") or "")


def _ui07_decision_entries(path: Path) -> list[dict[str, Any]]:
    """Decision entries tolerating the §7 wrapper and the legacy raw array.

    The console POST writes the wrapper; agents historically wrote a raw
    array. Both round-trip through collect, so both read here byte-identical.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        entries = payload.get("decisions")
        if not isinstance(entries, list):
            raise ValueError(f"{path.name}: 'decisions' key must be a list")
        return [e for e in entries if isinstance(e, dict)]
    if isinstance(payload, list):
        return [e for e in payload if isinstance(e, dict)]
    raise ValueError(f"{path.name}: expected a JSON list or wrapper object")


def _ui07_batch_papers(batch_data: Any) -> list[dict[str, Any]]:
    if not isinstance(batch_data, dict):
        return []
    for key in ("papers", "items", "candidates", "records"):
        value = batch_data.get(key)
        if isinstance(value, list):
            return [p for p in value if isinstance(p, dict)]
    return []


def _ui07_parent_candidates(ws: Path, batch_data: Any) -> set[str] | None:
    """Accepted parent candidate ids via the registry, or None when unresolvable.

    Unresolvable parents are reported (WORKER_PARENT_UNRESOLVED), never
    invented — the worker layer refuses the same way.
    """
    if not isinstance(batch_data, dict):
        return None
    artifact_id = batch_data.get("artifact_id")
    if not artifact_id:
        return None
    try:
        registry = json.loads(
            (ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
        )
        entry = registry.get("artifacts", {}).get(artifact_id)
        envelope = json.loads((ws / str(entry["path"])).read_text(encoding="utf-8"))
        candidates = envelope.get("data", {}).get("candidates", [])
        return {str(c.get("study_id")) for c in candidates if isinstance(c, dict)}
    except Exception:  # noqa: BLE001 - any resolution failure is "unresolvable"
        return None


def _ui07_batch_binding(ws: Path, batch_data: Any) -> dict[str, Any] | None:
    """STALE_BINDING iff the registered parent envelope changed after acceptance.

    Mirrors the registry's own freshness check (contracts.acceptance:
    canonical_fingerprint(parent_raw) vs the recorded sha256,
    REGISTERED_PARENT_HASH_MISMATCH): the recorded hash is over canonical
    bytes, so the live envelope is parsed and re-canonicalized — never
    raw-byte compared. A current binding carries no member at all; an
    unresolvable parent carries no binding claim either (it is reported
    in `missing` instead).
    """
    if not isinstance(batch_data, dict):
        return None
    artifact_id = batch_data.get("artifact_id")
    if not artifact_id:
        return None
    try:
        from scholar_harness.contracts.canonical import canonical_fingerprint

        registry = json.loads(
            (ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
        )
        entry = registry.get("artifacts", {}).get(artifact_id)
        live_raw = json.loads((ws / str(entry["path"])).read_text(encoding="utf-8"))
        if canonical_fingerprint(live_raw) != entry.get("sha256"):
            return {
                "state": "STALE_BINDING",
                "reason": "Parent batch superseded after acceptance; re-resolve before approval.",
            }
        return None
    except Exception:  # noqa: BLE001 - unreadable registry/envelope is no binding claim
        return None


def _ui07_terminal() -> frozenset:
    from scholar_harness.authority.review import TERMINAL_DECISIONS

    return TERMINAL_DECISIONS


def _ui07_batch_entry(
    ws: Path,
    manifest_row: dict[str, Any] | None,
    batch_index: int,
    missing: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """One §3(b) batch envelope, or None with a missing entry when the file is absent."""
    from scholar_harness.screening.integrity import (
        COVERAGE_INCOMPLETE,
        DUPLICATE_ENTRY,
        ScreeningIntegrityRefused,
        check_exact_coverage,
    )

    sdir = _ui07_screening_dir(ws)
    batch_file = sdir / f"batch_{batch_index:03d}.json"
    if not batch_file.is_file():
        missing.append({"file": batch_file.name, "reason": "BATCH_MISSING"})
        return None
    try:
        batch_data = json.loads(batch_file.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise _ui07_error(
            500,
            "UNPARSEABLE_JSON",
            f"unparseable JSON: {batch_file.name} ({exc})",
            file=batch_file.name,
        ) from exc

    papers = _ui07_batch_papers(batch_data)
    item_keys = [str(p.get("workspace_id") or p.get("study_id") or "") for p in papers]

    decisions_file = sdir / f"batch_{batch_index:03d}_decisions.json"
    entries: list[dict[str, Any]] | None = None
    if decisions_file.is_file():
        try:
            entries = _ui07_decision_entries(decisions_file)
        except Exception as exc:  # noqa: BLE001
            raise _ui07_error(
                500,
                "UNPARSEABLE_JSON",
                f"unparseable JSON: {decisions_file.name} ({exc})",
                file=decisions_file.name,
            ) from exc

    terminal = _ui07_terminal()
    candidates = _ui07_parent_candidates(ws, batch_data)
    coverage = "COMPLETE"
    extra: dict[str, Any] = {}
    if entries is None:
        coverage = "INCOMPLETE"
        extra = {"missing_ids": sorted(k for k in item_keys if k), "extra_ids": []}
        missing.append({"batch": batch_file.name, "reason": "NO_DECISIONS_YET"})
    elif candidates is None:
        coverage = "INCOMPLETE"
        extra = {"missing_ids": [], "extra_ids": []}
        if isinstance(batch_data, dict) and not batch_data.get("artifact_id"):
            missing.append({"batch": batch_file.name, "reason": "NO_PARENT_ARTIFACT"})
        else:
            missing.append(
                {"batch": batch_file.name, "reason": "WORKER_PARENT_UNRESOLVED"}
            )
    else:
        try:
            check_exact_coverage(set(candidates), entries)
        except ScreeningIntegrityRefused as exc:
            coverage = "INCOMPLETE"
            if exc.code == COVERAGE_INCOMPLETE:
                extra = {
                    "missing_ids": sorted(exc.details.get("missing_study_ids", [])),
                    "extra_ids": sorted(exc.details.get("extra_study_ids", [])),
                }
            elif exc.code == DUPLICATE_ENTRY:
                extra = {"missing_ids": [], "extra_ids": []}
                missing.append({"batch": batch_file.name, "reason": DUPLICATE_ENTRY})
            else:  # pragma: no cover - defensive: integrity adds no other code today
                extra = {"missing_ids": [], "extra_ids": []}
                missing.append({"batch": batch_file.name, "reason": exc.code})

    unresolved = (
        sorted(
            {
                _ui07_row_key(e)
                for e in entries
                if str(e.get("decision", "")).strip().upper() not in terminal
            }
            - {""}
        )
        if entries is not None
        else []
    )
    # "collected" is the collect-path acceptance (MANIFEST accepted lineage),
    # not mere sidecar presence: decisions can exist while uncollected (§4 stale).
    collected = bool(
        manifest_row is not None
        and (
            "decision_file_sha256" in manifest_row
            or "decisions_artifact_id" in manifest_row
        )
    )
    binding = _ui07_batch_binding(ws, batch_data)
    entry: dict[str, Any] = {
        "batch_index": batch_index,
        "batch_file": batch_file.name,
        "items": len(papers),
        "decisions_file": decisions_file.name if entries is not None else None,
        "decisions_count": len(entries) if entries is not None else None,
        "collected": collected,
        "coverage": coverage,
        "unresolved_rows": unresolved,
    }
    if coverage == "INCOMPLETE":
        entry.update(extra)
    if binding is not None:
        entry["binding"] = binding
    return entry


@router.get("/ui/batches")
def ui07_screening_batches(request: Request):
    """§3(b)/§4: screening batches envelope (populated, empty, stale)."""
    _ui07_refuse_caller_identity(request)
    ws = _ui07_ws(request)
    manifest, manifest_missing = _ui07_manifest(ws)
    missing: list[dict[str, Any]] = []
    if manifest is None:
        missing.append(
            manifest_missing
            or {"file": "literature/screening/MANIFEST.json", "reason": "NOT_PREPARED"}
        )
        return {
            "shape": "ui07.screening-batches-v1",
            "run_id": None,
            "count": 0,
            "batches": [],
            "missing": missing,
        }

    run_id = manifest.get("screening_run_id")
    rows = manifest.get("batches", [])
    if not isinstance(run_id, str) or not run_id or not isinstance(rows, list):
        missing.append(
            {"file": "literature/screening/MANIFEST.json", "reason": "NOT_PREPARED"}
        )
        return {
            "shape": "ui07.screening-batches-v1",
            "run_id": None,
            "count": 0,
            "batches": [],
            "missing": missing,
        }

    by_index = {r.get("batch_index"): r for r in rows if isinstance(r, dict)}
    batches: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            idx = int(row.get("batch_index"))
        except (TypeError, ValueError):
            continue
        item = _ui07_batch_entry(ws, by_index.get(idx), idx, missing)
        if item is not None:
            batches.append(item)
    batches.sort(key=lambda b: b["batch_index"])
    return {
        "shape": "ui07.screening-batches-v1",
        "run_id": run_id,
        "count": len(batches),
        "batches": batches,
        "missing": missing,
    }


def _ui07_worker_rows(ws: Path, batch_index: int) -> dict[str, dict[str, Any]]:
    """Worker recommendation rows keyed by study id (empty when none stored)."""
    from scholar_harness.screening.worker import (
        RECOMMENDATION_SCHEMA,
        recommendation_path,
    )

    path = recommendation_path(ws, batch_index)
    if not path.is_file():
        return {}
    payload = _ui07_read_json(path, missing_code="WORKER_BATCH_MISSING")
    if not isinstance(payload, dict) or payload.get("schema") != RECOMMENDATION_SCHEMA:
        return {}
    rows = payload.get("rows", [])
    out: dict[str, dict[str, Any]] = {}
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, dict) and _ui07_row_key(row):
            out[_ui07_row_key(row)] = row
    return out


def _ui07_join_row(
    paper: dict[str, Any],
    decision_entry: dict[str, Any] | None,
    worker_row: dict[str, Any] | None,
    missing: list[dict[str, Any]],
) -> dict[str, Any]:
    """One ui07.screening-row-v1: stored bytes joined, nothing re-derived.

    Precedence per stored layer: researcher decisions sidecar, then worker
    recommendation, then the explicit PENDING default the spec sanctions for
    rows with no researcher act (never a defaulted INCLUDE). Absent
    abstracts/locators are explicit `missing` entries, never placeholders.
    """
    from scholar_harness.screening.worker import (
        PENDING_DECISION,
        UNREVIEWED_UNCERTAINTY,
    )

    key = str(paper.get("workspace_id") or paper.get("study_id") or "")
    row: dict[str, Any] = {"shape": "ui07.screening-row-v1", "study_id": key}
    if paper.get("workspace_id"):
        row["workspace_id"] = str(paper["workspace_id"])

    citation = paper.get("citation")
    if isinstance(citation, str) and citation:
        row["citation"] = citation
    elif isinstance(paper.get("title"), str) and paper.get("title"):
        row["citation"] = paper["title"]
    else:
        missing.append({"study": key, "reason": "NO_CITATION"})
    abstract = paper.get("abstract")
    if isinstance(abstract, str) and abstract:
        row["abstract"] = abstract
    else:
        missing.append({"study": key, "reason": "NO_ABSTRACT"})

    source = decision_entry if decision_entry is not None else worker_row
    if source is None:
        missing.append({"study": key, "reason": "NO_DECISIONS_YET"})
        row.update(
            {
                "decision": PENDING_DECISION,
                "reasons": [],
                "uncertainty": UNREVIEWED_UNCERTAINTY,
            }
        )
    else:
        decision = (
            str(source.get("decision", PENDING_DECISION) or PENDING_DECISION)
            .strip()
            .upper()
            or PENDING_DECISION
        )
        reasons = source.get("reasons")
        if not isinstance(reasons, list):
            text = source.get("screening_reasoning") or source.get("reason") or ""
            reasons = [str(text)] if isinstance(text, str) and text.strip() else []
        uncertainty = source.get("uncertainty")
        if not isinstance(uncertainty, str) or not uncertainty:
            confidence = source.get("confidence")
            uncertainty = (
                f"confidence {confidence}"
                if isinstance(confidence, (int, float))
                else UNREVIEWED_UNCERTAINTY
            )
        row.update(
            {
                "decision": decision,
                "reasons": [str(r) for r in reasons],
                "uncertainty": uncertainty,
            }
        )
        refs = None
        if isinstance(source.get("criterion_refs"), dict):
            refs = source["criterion_refs"]
        else:
            inc = source.get("matched_inclusion_criteria")
            exc = source.get("violated_exclusion_criteria")
            if isinstance(inc, list) or isinstance(exc, list):
                refs = {
                    "inclusion": [str(i) for i in inc] if isinstance(inc, list) else [],
                    "exclusion": [str(i) for i in exc] if isinstance(exc, list) else [],
                }
        if isinstance(refs, dict):
            row["criterion_refs"] = {
                "inclusion": [
                    str(i)
                    for i in refs.get("inclusion", [])
                    if isinstance(refs.get("inclusion"), list)
                ],
                "exclusion": [
                    str(i)
                    for i in refs.get("exclusion", [])
                    if isinstance(refs.get("exclusion"), list)
                ],
            }
        locators = (
            source.get("source_locators")
            if isinstance(source.get("source_locators"), dict)
            else None
        )
        if locators is None:
            locators = {}
            for lkey in ("doi", "url", "venue", "year"):
                value = paper.get(lkey)
                if value is not None:
                    locators[lkey] = value
            ext = (
                paper.get("external_ids")
                if isinstance(paper.get("external_ids"), dict)
                else {}
            )
            if "doi" not in locators and isinstance(ext.get("doi"), str):
                locators["doi"] = ext["doi"]
        if locators:
            row["source_locators"] = {
                k: v
                for k, v in locators.items()
                if k in ("doi", "url", "venue", "year")
            }
        else:
            missing.append({"study": key, "reason": "NO_SOURCE_LOCATORS"})
    return row


@router.get("/ui/batch/{n}/rows")
def ui07_batch_rows(request: Request, n: int, limit: int = 100, offset: int = 0):
    """§3(b) per-record rows: the stored join, paged with limit/offset (OQ-P1)."""
    _ui07_refuse_caller_identity(request)
    ws = _ui07_ws(request)
    sdir = _ui07_screening_dir(ws)
    batch_file = sdir / f"batch_{n:03d}.json"
    if not batch_file.is_file():
        raise _ui07_error(
            404,
            "BATCH_MISSING",
            f"missing file: batch_{n:03d}.json",
            file=batch_file.name,
        )
    batch_data = _ui07_read_json(batch_file, missing_code="BATCH_MISSING")
    papers = _ui07_batch_papers(batch_data)

    decisions_file = sdir / f"batch_{n:03d}_decisions.json"
    by_key: dict[str, dict[str, Any]] = {}
    if decisions_file.is_file():
        try:
            entries = _ui07_decision_entries(decisions_file)
        except Exception as exc:  # noqa: BLE001
            raise _ui07_error(
                500,
                "UNPARSEABLE_JSON",
                f"unparseable JSON: {decisions_file.name} ({exc})",
                file=decisions_file.name,
            ) from exc
        for entry in entries:
            if _ui07_row_key(entry):
                by_key[_ui07_row_key(entry)] = entry
    worker_rows = _ui07_worker_rows(ws, n)

    missing: list[dict[str, Any]] = []
    if not decisions_file.is_file() and not worker_rows:
        missing.append({"batch": batch_file.name, "reason": "NO_DECISIONS_YET"})
    joined = []
    for paper in papers:
        key = str(paper.get("workspace_id") or paper.get("study_id") or "")
        # Researcher decisions first, worker recommendation second, explicit
        # PENDING default only when neither layer stored the row.
        fallback = None if key in by_key else worker_rows.get(key)
        joined.append(_ui07_join_row(paper, by_key.get(key), fallback, missing))
    # Worker-only rows (recommendation covers a study the handoff papers omit)
    # are never invented into the join; coverage reports the gap instead.
    for key in worker_rows:
        if key and all(
            str(p.get("workspace_id") or p.get("study_id") or "") != key for p in papers
        ):
            missing.append({"study": key, "reason": "WORKER_ROW_WITHOUT_PAPER"})
    total = len(joined)
    page = joined[max(0, offset) : max(0, offset) + max(0, limit)]
    return {
        "shape": "ui07.screening-rows-v1",
        "batch_index": n,
        "batch_file": batch_file.name,
        "total": total,
        "offset": offset,
        "limit": limit,
        "rows": page,
        "missing": missing,
    }


@router.get("/ui/batch/{n}/review")
def ui07_batch_review(request: Request, n: int):
    """§3(d): recommendation, resolution, override history, review, deferral."""
    from scholar_harness.screening.worker import (
        RECOMMENDATION_SCHEMA,
        WORKER_METHOD,
        recommendation_path,
    )

    _ui07_refuse_caller_identity(request)
    ws = _ui07_ws(request)
    sdir = _ui07_screening_dir(ws)
    batch_file = sdir / f"batch_{n:03d}.json"
    if not batch_file.is_file():
        raise _ui07_error(
            404,
            "BATCH_MISSING",
            f"missing file: batch_{n:03d}.json",
            file=batch_file.name,
        )
    missing: list[dict[str, Any]] = []

    rec_path = recommendation_path(ws, n)
    if rec_path.is_file():
        rec_payload = _ui07_read_json(rec_path, missing_code="WORKER_BATCH_MISSING")
        if (
            isinstance(rec_payload, dict)
            and rec_payload.get("schema") == RECOMMENDATION_SCHEMA
        ):
            rec_rows = rec_payload.get("rows", [])
            rec_rows = (
                [r for r in rec_rows if isinstance(r, dict)]
                if isinstance(rec_rows, list)
                else []
            )
            terminal = _ui07_terminal()
            pending = sum(
                1
                for r in rec_rows
                if str(r.get("decision", "")).strip().upper() not in terminal
            )
            recommendation: dict[str, Any] = {
                "present": True,
                "schema": RECOMMENDATION_SCHEMA,
                "revision": int(rec_payload.get("recommendation_revision", 1)),
                "method": str(
                    (rec_payload.get("worker") or {}).get("method", WORKER_METHOD)
                )
                if isinstance(rec_payload.get("worker"), dict)
                else WORKER_METHOD,
                "rows_pending": pending,
            }
        else:
            recommendation = {"present": False}
            missing.append(
                {"file": rec_path.name, "reason": "RECOMMENDATION_SCHEMA_MISMATCH"}
            )
    else:
        recommendation = {"present": False}
        missing.append({"file": rec_path.name, "reason": "WORKER_BATCH_MISSING"})

    decisions_file = sdir / f"batch_{n:03d}_decisions.json"
    if decisions_file.is_file():
        try:
            entries = _ui07_decision_entries(decisions_file)
        except Exception as exc:  # noqa: BLE001
            raise _ui07_error(
                500,
                "UNPARSEABLE_JSON",
                f"unparseable JSON: {decisions_file.name} ({exc})",
                file=decisions_file.name,
            ) from exc
        terminal = _ui07_terminal()
        unresolved = sorted(
            {
                _ui07_row_key(e)
                for e in entries
                if str(e.get("decision", "")).strip().upper() not in terminal
            }
            - {""}
        )
        resolution = {
            "resolved": len(entries) - len(unresolved),
            "total": len(entries),
            "unresolved_rows": unresolved,
        }
    else:
        batch_data = _ui07_read_json(batch_file, missing_code="BATCH_MISSING")
        total = len(_ui07_batch_papers(batch_data))
        resolution = {"resolved": 0, "total": total, "unresolved_rows": []}
        missing.append({"batch": batch_file.name, "reason": "NO_DECISIONS_YET"})

    # Override history reports the AG-03B supersede chain without rewriting it.
    from scholar_harness.authority.review import REVIEW_SCHEMA

    review_path = sdir / "reviews" / f"batch_{n:03d}_review.json"
    if review_path.is_file():
        review_payload = _ui07_read_json(review_path, missing_code="BATCH_MISSING")
        if (
            isinstance(review_payload, dict)
            and review_payload.get("schema") == REVIEW_SCHEMA
        ):
            superseded = bool(review_payload.get("superseded"))
            override: dict[str, Any] = {"superseded": superseded}
            if superseded:
                override.update(
                    {
                        "snapshot_fingerprint": str(
                            review_payload.get("snapshot_fingerprint")
                        ),
                        "recommendation_sha256": str(
                            review_payload.get("recommendation_sha256")
                        ),
                        "final_decision_sha256": str(
                            review_payload.get("final_decision_sha256")
                        ),
                    }
                )
        else:
            override = {"superseded": False}
            missing.append(
                {
                    "file": f"reviews/{review_path.name}",
                    "reason": "REVIEW_SCHEMA_MISMATCH",
                }
            )
    else:
        override = {"superseded": False}

    from scholar_harness.authority.binding import content_sha256
    from scholar_harness.authority.review import BATCH_APPROVAL_SCHEMA, DEFERRAL_SCHEMA

    approval_path = sdir / "approvals" / f"batch_{n:03d}_approval.json"
    if approval_path.is_file():
        approval_payload = _ui07_read_json(approval_path, missing_code="BATCH_MISSING")
        if (
            isinstance(approval_payload, dict)
            and approval_payload.get("schema") == BATCH_APPROVAL_SCHEMA
        ):
            review_state = {
                "present": True,
                "approval_fingerprint": content_sha256(approval_path.read_bytes()),
            }
        else:
            review_state = {"present": False}
            missing.append(
                {
                    "file": f"approvals/{approval_path.name}",
                    "reason": "APPROVAL_SCHEMA_MISMATCH",
                }
            )
    else:
        review_state = {"present": False}

    deferral_path = sdir / "deferrals" / f"batch_{n:03d}_deferral.json"
    if deferral_path.is_file():
        deferral_payload = _ui07_read_json(deferral_path, missing_code="BATCH_MISSING")
        if (
            isinstance(deferral_payload, dict)
            and deferral_payload.get("schema") == DEFERRAL_SCHEMA
        ):
            deferral: dict[str, Any] = {"present": True}
        else:
            deferral = {"present": False}
            missing.append(
                {
                    "file": f"deferrals/{deferral_path.name}",
                    "reason": "DEFERRAL_SCHEMA_MISMATCH",
                }
            )
    else:
        deferral = {"present": False}

    return {
        "shape": "ui07.review-state-v1",
        "batch_index": n,
        "recommendation": recommendation,
        "resolution": resolution,
        "override": override,
        "review": review_state,
        "deferral": deferral,
        "missing": missing,
    }


@router.get("/ui/batch/{n}/criterion-refs")
def ui07_criterion_refs(request: Request, n: int):
    """§3(c): criteria from the batch envelope + sources with stored locators."""
    _ui07_refuse_caller_identity(request)
    ws = _ui07_ws(request)
    sdir = _ui07_screening_dir(ws)
    batch_file = sdir / f"batch_{n:03d}.json"
    if not batch_file.is_file():
        raise _ui07_error(
            404,
            "BATCH_MISSING",
            f"missing file: batch_{n:03d}.json",
            file=batch_file.name,
        )
    batch_data = _ui07_read_json(batch_file, missing_code="BATCH_MISSING")
    missing: list[dict[str, Any]] = []

    criteria = (
        (batch_data.get("protocol") or {}).get("screening_criteria")
        if isinstance(batch_data, dict)
        else None
    )
    criteria = criteria if isinstance(criteria, dict) else {}
    inclusion = [
        {
            "id": str(item.get("id")),
            "text": str(item.get("text") or item.get("criterion") or ""),
        }
        for item in criteria.get("inclusion", [])
        if isinstance(item, dict) and item.get("id")
    ]
    exclusion = [
        {
            "id": str(item.get("id")),
            "text": str(item.get("text") or item.get("criterion") or ""),
        }
        for item in criteria.get("exclusion", [])
        if isinstance(item, dict) and item.get("id")
    ]

    # Protocol fingerprint: the envelope's recorded scope first (the scope the
    # worker preserved), live protocol.json only as fallback. OQ-P2 drift is
    # reported, never silently chosen.
    envelope_fp: str | None = None
    try:
        registry = json.loads(
            (ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
        )
        artifact_id = (
            batch_data.get("artifact_id") if isinstance(batch_data, dict) else None
        )
        envelope = json.loads(
            (
                ws / str(registry.get("artifacts", {}).get(artifact_id, {}).get("path"))
            ).read_text(encoding="utf-8")
        )
        envelope_fp = envelope.get("protocol_fingerprint")
    except Exception:  # noqa: BLE001 - unresolvable envelope is explicit below
        envelope_fp = None
    live_fp: str | None = None
    try:
        from scholar_protocol.canonical import canonical_fingerprint as _protocol_fp
        from scholar_protocol.models import ResearchProtocol

        live_fp = _protocol_fp(
            ResearchProtocol.model_validate(
                json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
            )
        )
    except Exception:  # noqa: BLE001
        live_fp = None
    protocol_fingerprint = envelope_fp or live_fp
    if protocol_fingerprint is None:
        missing.append(
            {"batch": batch_file.name, "reason": "PROTOCOL_FINGERPRINT_UNAVAILABLE"}
        )
    elif envelope_fp and live_fp and envelope_fp != live_fp:
        missing.append(
            {"batch": batch_file.name, "reason": "PROTOCOL_FINGERPRINT_DRIFT"}
        )

    verified_by_id: dict[str, dict[str, Any]] = {}
    verified_path = ws / "literature" / "verified.json"
    if verified_path.is_file():
        try:
            verified_rows = json.loads(verified_path.read_text(encoding="utf-8"))
            for row in verified_rows if isinstance(verified_rows, list) else []:
                if isinstance(row, dict) and row.get("workspace_id"):
                    verified_by_id[str(row["workspace_id"])] = row
        except Exception:  # noqa: BLE001 - unreadable verified material is explicit
            missing.append(
                {"file": "literature/verified.json", "reason": "UNPARSEABLE_JSON"}
            )
    else:
        missing.append(
            {"file": "literature/verified.json", "reason": "VERIFIED_MATERIAL_ABSENT"}
        )

    sources: list[dict[str, Any]] = []
    for paper in _ui07_batch_papers(batch_data):
        key = str(paper.get("workspace_id") or paper.get("study_id") or "")
        verified = verified_by_id.get(key, {})
        verified_ids = (
            verified.get("external_ids")
            if isinstance(verified.get("external_ids"), dict)
            else {}
        )
        source: dict[str, Any] = {"workspace_id": key}
        citation = paper.get("citation") or paper.get("title") or verified.get("title")
        if isinstance(citation, str) and citation:
            source["citation"] = citation
        else:
            missing.append({"study": key, "reason": "NO_CITATION"})
        abstract = paper.get("abstract") or verified.get("abstract")
        if isinstance(abstract, str) and abstract:
            source["abstract"] = abstract
        else:
            missing.append({"study": key, "reason": "NO_ABSTRACT"})
        for lkey in ("doi", "url", "venue", "year"):
            value = paper.get(
                lkey,
                verified.get(lkey, verified_ids.get("doi") if lkey == "doi" else None),
            )
            if value is not None:
                source[lkey] = value
        if not any(k in source for k in ("doi", "url", "venue", "year")):
            missing.append({"study": key, "reason": "NO_SOURCE_LOCATORS"})
        sources.append(source)

    payload: dict[str, Any] = {
        "shape": "ui07.criterion-refs-v1",
        "protocol_fingerprint": protocol_fingerprint,
        "inclusion": inclusion,
        "exclusion": exclusion,
        "sources": sources,
        "missing": missing,
    }
    if envelope_fp and live_fp and envelope_fp != live_fp:
        payload["live_protocol_fingerprint"] = live_fp
    return payload


#: Journey-scoped actions for the §3(f) audit feed (projection of the
#: journal; the UI never rewrites, reorders, or appends events).
_UI07_JOURNEY_ACTIONS = frozenset(
    {"SCREEN_DECISIONS", "SCREENING_GENERATION_PUBLISHED"}
)


@router.get("/ui/audit-feed")
def ui07_audit_feed(
    request: Request,
    action: str | None = None,
    agent: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """§3(f): newest-first screening-journey audit projection (bad lines skipped)."""
    _ui07_refuse_caller_identity(request)
    ws = _ui07_ws(request)
    journal = ws / "audit" / "journal.jsonl"
    items: list[dict[str, Any]] = []
    if journal.is_file():
        for line in journal.read_text(encoding="utf-8").strip().splitlines():
            if not line.strip():
                continue
            try:
                evt = json.loads(line)
            except Exception:  # noqa: BLE001 - one bad line never refuses the feed
                logger.debug("skipping unparseable journal line", exc_info=True)
                continue
            if not isinstance(evt, dict):
                continue
            evt_action = str(evt.get("action", ""))
            if action is not None:
                if evt_action != action.upper():
                    continue
            elif evt_action not in _UI07_JOURNEY_ACTIONS and not evt_action.startswith(
                "SCREENING_"
            ):
                continue
            if agent and evt.get("agent_or_tool") != agent:
                continue
            items.append(
                {
                    "timestamp": evt.get("timestamp"),
                    "event_id": evt.get("event_id"),
                    "action": evt_action,
                    "agent_or_tool": evt.get("agent_or_tool"),
                    "description": evt.get("description"),
                    "status": evt.get("status"),
                }
            )
    items = items[::-1]
    return {
        "shape": "ui07.audit-feed-v1",
        "total": len(items),
        "offset": offset,
        "limit": limit,
        "items": items[offset : offset + limit],
    }


# ---------------------------------------------------------------------------
# UI-07 protected action API (pairing-code approval; RELEASE lane).
#
# Action routes live under `/actions/` — clearly distinct from the `/ui/`
# read routes above. The five operations of the action spec (§1) map as:
#
# * draft capture / override-as-draft — REUSE of the existing
#   `POST /api/v1/screening/batch/{n}/decisions` route, which writes draft
#   decision files only. There is deliberately NO `/actions/drafts` route:
#   a second writer would be a second approval-shaped surface to review, so
#   the reuse is documented here and pinned by test (unknown route → 404).
# * approval request — `POST /actions/pairing/redeem` (this section). There
#   is deliberately NO mint/create pairing route: challenge creation is the
#   terminal-side `pairing.begin_pairing` act (`approve --begin` semantics)
#   and no endpoint ever returns a plaintext code (pinned by test).
# * defer / cancel drafts — `POST /actions/defer` → AG-04 `defer_command`
#   semantics (reused, never rewritten), plus voiding the staged pairing.
# * publication trigger — `POST /actions/publish` → the existing gated
#   `cmd_collect` path in-process (reused, never duplicated).
# * challenge state — `GET /actions/pairing/status` (safe status only:
#   state/expiry/snapshot-fingerprint, NEVER code or hash).
#
# Every action request takes an optional `request_id` and every action
# response returns one; journal rows carry it in `parameters`. `request_id`
# is correlation-only: a client-supplied log/journal trace handle, never
# identity, never authorization, never a secret. The server never trusts it
# for auth; redeem idempotency treats it as a stem only — the same stem
# with different content hashes refuses instead of replaying an earlier
# success, an absent stem proceeds normally, and a fresh id always mints
# through the normal consumed/single-use path. Browser-held
# identity is never trusted: bodies use `extra="ignore"` so caller-minted
# names/roles/reviewer strings are dropped, and the query guard refuses
# caller-minted fingerprints. Pairing codes are accepted only with a
# loopback (or absent, i.e. non-browser) Origin (§3.6); cross-origin browser
# POSTs additionally stay preflight-blocked by the frozen CORS middleware in
# `console/serve.py` (GET-only), which this packet does not own — a
# same-origin route or a CORS follow-up is required before a browser can
# POST these routes cross-origin (recorded residual, not silently fixed).
# ---------------------------------------------------------------------------

#: Journal code for an action whose provenance row could not be recorded.
ACTION_AUDIT_FAILED = "ACTION_AUDIT_FAILED"


class RedeemBody(BaseModel):
    model_config = ConfigDict(extra="ignore")

    batch: int
    code: str
    request_id: str | None = None


class DeferActionBody(BaseModel):
    model_config = ConfigDict(extra="ignore")

    batch: int
    reason: str = ""
    request_id: str | None = None


class PublishActionBody(BaseModel):
    model_config = ConfigDict(extra="ignore")

    request_id: str | None = None


def _action_request_id(value: str | None) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return f"REQ-{uuid.uuid4().hex[:12]}"


def _require_action_origin(request: Request) -> None:
    """Refuse action requests carrying a non-loopback Origin (spec §3.6).

    Mirrors the loopback shape of the frozen CORS middleware: absent Origin
    (non-browser clients) passes through, loopback origins pass, anything
    else refuses with a typed 403 before any state is touched.
    """
    import re

    origin = request.headers.get("origin")
    if origin is None:
        return
    if re.match(
        r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        origin.strip(),
        re.IGNORECASE,
    ):
        return
    raise _ui07_error(
        403,
        "ACTION_ORIGIN_REFUSED",
        "refusing action request from a non-loopback origin; pairing codes "
        "are accepted only over the loopback binding",
        origin=origin,
    )


def _action_http_error(exc: Exception, request_id: str) -> HTTPException:
    """Map a typed authority/integrity/worker refusal to a typed HTTP error."""
    code = str(getattr(exc, "code", None) or "ACTION_FAILED")
    message = str(getattr(exc, "message", None) or str(exc) or code)
    try:
        details = dict(getattr(exc, "details", None) or {})
    except (TypeError, ValueError):
        details = {}
    details.setdefault("request_id", request_id)
    if code in ("PAIRING_CODE_INVALID",):
        status = 403
    elif code in ("APPROVAL_NOT_OPERATOR", "OPERATOR_CONTEXT_MISSING"):
        status = 403
    elif code in (
        "COVERAGE_INCOMPLETE",
        "DUPLICATE_ENTRY",
        "UNRESOLVED_FINALIZE_REFUSED",
        "REVIEW_INVALID_DECISIONS",
        "REVIEW_CHECKLIST_UNSUPPORTED",
        "REVIEW_DUAL_UNSUPPORTED",
        "REVIEW_REASON_MISSING",
        "REVIEW_NOT_PREPARED",
    ):
        status = 422
    elif code in ("WORKER_BATCH_MISSING", "BATCH_MISSING"):
        status = 404
    elif code in ("PROMOTION_AUDIT_FAILED", ACTION_AUDIT_FAILED):
        status = 500
    else:
        # STALE_VIEW, APPROVAL_CONTENT_CHANGED/SCOPE/MISSING, worker parents,
        # generation lock/currentness: state conflicts, never silent success.
        status = 409
    return _ui07_error(status, code, message, **details)


def _journal_action(
    ws: Path,
    *,
    action: str,
    description: str,
    request_id: str,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    parameters: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    status: str = "SUCCESS",
) -> dict[str, Any]:
    """Journal one action row through the shared service (never any code)."""
    params = dict(parameters or {})
    params["request_id"] = request_id
    return log_event(
        workspace=ws,
        action=action,
        description=description,
        inputs=inputs or [],
        outputs=outputs or [],
        parameters=params,
        metrics=metrics or {},
        status=status,
    )


def _snapshot_file(path: Path) -> bytes | None:
    try:
        return path.read_bytes() if path.is_file() else None
    except OSError:
        return None


def _restore_file(path: Path, blob: bytes | None) -> None:
    try:
        if blob is None:
            if path.is_file():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob)
    except OSError:
        pass


@router.get("/actions/pairing/status")
def action_pairing_status(
    request: Request, batch: int = 0, request_id: str | None = None
) -> dict[str, Any]:
    """Safe challenge status: state/expiry/fingerprint, NEVER code or hash."""
    from scholar_harness.authority import pairing as _pairing

    _require_action_origin(request)
    _ui07_refuse_caller_identity(request)
    ws = _ui07_ws(request)
    if not (ws / "literature" / "screening" / f"batch_{batch:03d}.json").is_file():
        raise _ui07_error(
            404,
            "BATCH_MISSING",
            f"missing file: batch_{batch:03d}.json",
            file=f"batch_{batch:03d}.json",
        )
    payload = _pairing.pairing_status(ws, batch)
    payload["request_id"] = _action_request_id(request_id)
    return payload


@router.post("/actions/pairing/redeem", status_code=200)
def action_pairing_redeem(body: RedeemBody, request: Request) -> dict[str, Any]:
    """Verify a transcribed pairing code; mint the approval via AG-03B."""
    from scholar_harness.authority import pairing as _pairing
    from scholar_harness.authority.binding import AuthorityRefused
    from scholar_harness.authority.review import (
        ReviewRefused,
        batch_approval_path,
        deferral_path,
        review_path,
    )
    from scholar_harness.screening.integrity import ScreeningIntegrityRefused
    from scholar_harness.screening.worker import WorkerRefused
    from scholar_harness.verification_identity import VerificationIdentityRefused

    _require_action_origin(request)
    _ui07_refuse_caller_identity(request)
    ws = _ui07_ws(request)
    req = _action_request_id(body.request_id)

    # Fail-closed rollback set: every file the mint may create, replace, or
    # lift, snapshotted before the mint so a journal failure restores the
    # pre-request state (the staged challenge bytes included).
    watched = [
        review_path(ws, body.batch),
        batch_approval_path(ws, body.batch),
        ws / "literature" / "screening" / "publication_approval.json",
        deferral_path(ws, body.batch),
        _pairing.pairing_path(ws, body.batch),
    ]
    backup = {path: _snapshot_file(path) for path in watched}

    try:
        result = _pairing.redeem_pairing(
            ws, body.batch, body.code or "", request_id=req
        )
    except (
        AuthorityRefused,
        ReviewRefused,
        ScreeningIntegrityRefused,
        WorkerRefused,
        VerificationIdentityRefused,
    ) as exc:
        raise _action_http_error(exc, req) from exc

    try:
        event = _journal_action(
            ws,
            action="SCREENING_PAIRING_REDEEMED",
            description=(
                f"Redeemed pairing challenge for batch {body.batch} "
                f"(approval {result['approval_fingerprint']})"
            ),
            request_id=req,
            inputs=[f"batch_{body.batch:03d}.json"],
            outputs=[f"batch_{body.batch:03d}_approval.json"],
            parameters={
                "batch_index": body.batch,
                "snapshot_fingerprint": result["snapshot_fingerprint"],
                "approval_fingerprint": result["approval_fingerprint"],
                "operator_identity": result["operator_identity"],
                "superseded": result["superseded"],
            },
            metrics={"batch_index": body.batch},
        )
    except OSError as exc:
        for path, blob in backup.items():
            _restore_file(path, blob)
        raise _ui07_error(
            500,
            ACTION_AUDIT_FAILED,
            "provenance could not be recorded; the approval was rolled back "
            "and nothing was published",
            request_id=req,
        ) from exc
    return {
        "shape": "screening-action-redeem-v1",
        "request_id": req,
        "journal_event_id": event["event_id"],
        **result,
    }


@router.post("/actions/defer", status_code=200)
def action_defer_batch(body: DeferActionBody, request: Request) -> dict[str, Any]:
    """Defer/cancel with reason (AG-04 semantics) and void the challenge."""
    from scholar_harness.authority.review import ReviewRefused, defer_command

    _require_action_origin(request)
    _ui07_refuse_caller_identity(request)
    ws = _ui07_ws(request)
    req = _action_request_id(body.request_id)
    try:
        out = defer_command(ws, body.batch, reason=body.reason or "")
    except ReviewRefused as exc:
        raise _action_http_error(exc, req) from exc
    # F-01: defer_command owns staged-state teardown and records
    # pairing_voided in the deferral file. No second cancel here: it would
    # misreport (already-consumed reads False) and could void a fresh
    # challenge staged after the deferral.
    try:
        record = json.loads(out.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise _ui07_error(
            500,
            ACTION_AUDIT_FAILED,
            f"deferral record unreadable ({exc})",
            request_id=req,
        ) from exc
    pairing_voided = bool(record.get("pairing_voided", False))
    # The deferral stands even if this row fails: deferring publishes
    # nothing, so the safe direction needs no rollback — but the failure
    # still surfaces instead of reporting success.
    try:
        event = _journal_action(
            ws,
            action="SCREENING_BATCH_DEFERRED",
            description=(
                f"Deferred batch {body.batch}: {record.get('reason')} "
                "(nothing published)"
            ),
            request_id=req,
            inputs=[f"batch_{body.batch:03d}.json"],
            outputs=[out.name],
            parameters={
                "batch_index": body.batch,
                "reason": record.get("reason"),
                "cancelled": record.get("cancelled"),
                "pairing_voided": pairing_voided,
            },
            metrics={"batch_index": body.batch},
        )
    except OSError as exc:
        raise _ui07_error(
            500,
            ACTION_AUDIT_FAILED,
            "provenance could not be recorded; the batch stays deferred "
            "(nothing was published)",
            request_id=req,
        ) from exc
    return {
        "shape": "screening-action-defer-v1",
        "request_id": req,
        "batch_index": body.batch,
        "deferral_file": out.name,
        "reason": record.get("reason"),
        "cancelled": record.get("cancelled"),
        "pairing_voided": pairing_voided,
        "journal_event_id": event["event_id"],
    }


@router.post("/actions/publish", status_code=200)
def action_publish_screening(
    body: PublishActionBody, request: Request
) -> dict[str, Any]:
    """Run the existing gated collect path in-process; the browser never writes."""
    from scholar_harness.authority.binding import AuthorityRefused
    from scholar_harness.authority.generations import (
        GenerationStatus,
        require_current_generation,
    )
    from scholar_harness.screening.collector import cmd_collect

    _require_action_origin(request)
    _ui07_refuse_caller_identity(request)
    ws = _ui07_ws(request)
    req = _action_request_id(body.request_id)
    try:
        cmd_collect(ws)
    except AuthorityRefused as exc:
        raise _action_http_error(exc, req) from exc
    except Exception as exc:  # noqa: BLE001 - collect fails closed by design
        code = str(getattr(exc, "code", None) or "COLLECT_REFUSED")
        if isinstance(exc, SystemExit):
            raise _ui07_error(
                404,
                "NOT_PREPARED",
                "workspace has no prepared screening batches",
                request_id=req,
            ) from exc
        raise _ui07_error(
            409,
            code,
            str(exc) or code,
            request_id=req,
        ) from exc
    current = require_current_generation(ws)
    if current.status is not GenerationStatus.CURRENT or current.record is None:
        raise _ui07_error(
            500,
            ACTION_AUDIT_FAILED,
            "collect returned without a CURRENT generation; refusing to report success",
            request_id=req,
            status=current.status.value,
        )
    record = current.record
    try:
        event = _journal_action(
            ws,
            action="SCREENING_PUBLISH_COMPLETED",
            description=(
                f"Published authorized screening generation "
                f"{record.generation_id} via the action API"
            ),
            request_id=req,
            outputs=["literature/screening/generation.json"],
            parameters={
                "generation_id": record.generation_id,
                "generation_fingerprint": record.fingerprint(),
                "approval_fingerprint": record.approval_fingerprint,
            },
            metrics={"output_count": len(record.output_digests)},
        )
    except OSError as exc:
        # The generation stands (collect already committed it); a retry joins
        # it idempotently, so surfacing — not swallowing — is the safe move.
        raise _ui07_error(
            500,
            ACTION_AUDIT_FAILED,
            "generation is CURRENT but its action row could not be recorded; "
            "retry joins the same generation idempotently",
            request_id=req,
            generation_id=record.generation_id,
        ) from exc
    return {
        "shape": "screening-action-publish-v1",
        "request_id": req,
        "status": current.status.value,
        "generation_id": record.generation_id,
        "generation_fingerprint": record.fingerprint(),
        "outputs": dict(record.output_digests),
        "journal_event_id": event["event_id"],
    }
