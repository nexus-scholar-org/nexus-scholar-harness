"""Read-only endpoints over the canonical workspace contract (SPECS section 3).

Every response returns canonical file contents (or a 404 listing the missing
relative path). No console-owned state is involved: these are thin views over
the same files agents read.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from ..runtimes.actions import actions_payload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["workspace"])


def _ws(request: Request) -> Path:
    return Path(request.app.state.workspace).resolve()


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"missing file: {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"unparseable JSON: {path.name}"
        ) from exc


def _list_dir(parent: Path, pattern: str, suffix: str | None = None) -> list[str]:
    if not parent.is_dir():
        return []
    out = sorted(str(p.name) for p in parent.glob(pattern))
    if suffix:
        out = [n for n in out if n.endswith(suffix)]
    return out


def _safe_join(root: Path, filename: str) -> Path:
    """Join a plain filename under root, rejecting any traversal."""
    if (
        "/" in filename
        or "\\" in filename
        or ".." in filename
        or filename in ("", ".", "..")
    ):
        raise HTTPException(status_code=400, detail=f"invalid file name: {filename}")
    return root / filename


def _markdown_kind(prefixes: dict[str, str], name: str) -> str:
    for prefix, kind in prefixes.items():
        if name.startswith(prefix):
            return kind
    return "other"


SYNTHESIS_KINDS = {
    "consensus": "consensus",
    "evidence": "matrix",
    "synthesis_matrix": "matrix",
    "rag_rq": "rq_review",
    "synthesis_rq": "rq_review",
    "literature_review": "review",
}

PHASE4_KINDS = {
    "trust_consensus": "trust",
    "risk_of_bias": "rob",
    "coi": "coi",
    "open_science": "open_science",
    "retraction": "retraction",
}


def _file_index(dir_path: Path, kinds: dict[str, str]) -> list[dict[str, Any]]:
    if not dir_path.is_dir():
        return []
    entries = []
    for p in sorted(dir_path.iterdir()):
        if not p.is_file() or p.name.startswith("."):
            continue
        ext = p.suffix.lower()
        entries.append(
            {
                "name": p.name,
                "kind": _markdown_kind(kinds, p.name),
                "ext": ext,
                "is_markdown": ext == ".md",
                "size_bytes": p.stat().st_size,
                "mtime": p.stat().st_mtime,
            }
        )
    return entries


@router.get("/workspace/meta")
def workspace_meta(request: Request):
    ws = _ws(request)
    meta: dict[str, Any] = {"workspace": str(ws)}
    for name in ("project.json", "INDEX.md", "protocol.json"):
        path = ws / name
        if path.exists():
            meta[name] = path.read_text(encoding="utf-8")
        else:
            meta[name] = f"-> missing: {name}"
    return meta


@router.get("/workspace/status")
def workspace_status(request: Request):
    from scholar_harness.orchestrator import ResearchOrchestrator

    orchestrator = ResearchOrchestrator(_ws(request))
    return orchestrator.get_status()


@router.get("/literature/candidates")
def literature_candidates(request: Request, limit: int = 100, offset: int = 0):
    ws = _ws(request)
    raw = ws / "literature" / "raw_search.json"
    if not raw.exists():
        raise HTTPException(status_code=404, detail="missing file: raw_search.json")
    docs = _read_json(raw)
    total = len(docs)
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": docs[offset : offset + limit],
    }


@router.get("/literature/included")
def literature_included(request: Request):
    return _read_json(_ws(request) / "literature" / "included.json")


@router.get("/literature/excluded")
def literature_excluded(request: Request):
    return _read_json(_ws(request) / "literature" / "excluded.json")


@router.get("/screening/batches")
def screening_batches(request: Request):
    ws = _ws(request)
    sdir = ws / "literature" / "screening"
    batches = []
    for p in sorted(sdir.glob("batch_*.json")):
        if "_decisions" in p.name:
            continue
        decisions = sdir / (p.stem + "_decisions.json")
        batches.append(
            {
                "name": p.name,
                "items": _count_json(p),
                "decisions_file": decisions.name if decisions.exists() else None,
                "decisions_count": _count_json(decisions) if decisions.exists() else 0,
                "collected": decisions.exists(),
            }
        )
    return {"count": len(batches), "batches": batches}


def _count_json(path: Path) -> int:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            for key in ("items", "papers", "studies", "records"):
                if key in payload and isinstance(payload[key], list):
                    return len(payload[key])
            return 1
        if isinstance(payload, list):
            return len(payload)
        return 0
    except Exception:  # noqa: BLE001
        return 0


@router.get("/screening/batch/{n}")
def screening_batch(request: Request, n: int):
    ws = _ws(request)
    sdir = ws / "literature" / "screening"
    batch_file = sdir / f"batch_{n:03d}.json"
    if not batch_file.exists():
        raise HTTPException(status_code=404, detail=f"missing file: batch_{n:03d}.json")
    decisions_file = sdir / f"batch_{n:03d}_decisions.json"
    return {
        "batch_file": batch_file.name,
        "items": _read_json(batch_file),
        "decisions_file": decisions_file.name if decisions_file.exists() else None,
        "decisions": _read_json(decisions_file) if decisions_file.exists() else None,
    }


@router.get("/synthesis")
def synthesis_index(request: Request):
    return {
        "count": len(_file_index(_ws(request) / "synthesis", SYNTHESIS_KINDS)),
        "files": _file_index(_ws(request) / "synthesis", SYNTHESIS_KINDS),
    }


@router.get("/phase4")
def phase4_index(request: Request):
    return {
        "count": len(_file_index(_ws(request) / "phase4", PHASE4_KINDS)),
        "files": _file_index(_ws(request) / "phase4", PHASE4_KINDS),
    }


@router.get("/synthesis/{filename}")
def synthesis_file(request: Request, filename: str):
    path = _safe_join(_ws(request) / "synthesis", filename)
    if not path.is_file():
        raise HTTPException(
            status_code=404, detail=f"missing file: synthesis/{filename}"
        )
    return {"filename": filename, "content": path.read_text(encoding="utf-8")}


@router.get("/phase4/{filename}")
def phase4_file(request: Request, filename: str):
    path = _safe_join(_ws(request) / "phase4", filename)
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"missing file: phase4/{filename}")
    return {"filename": filename, "content": path.read_text(encoding="utf-8")}


@router.get("/harvest/corpus")
def harvest_corpus(request: Request):
    ws = _ws(request)
    pdf_dir = ws / "pdfs"
    extracted_dir = ws / "extracted"
    pdfs = []
    if pdf_dir.is_dir():
        for p in sorted(pdf_dir.glob("*.pdf")):
            pdfs.append({"name": p.name, "size_bytes": p.stat().st_size})
    extracted = []
    if extracted_dir.is_dir():
        for p in sorted(extracted_dir.glob("*.md")):
            extracted.append({"name": p.name})
    manifest = ws / "literature" / "pdf_manifest.json"
    return {
        "pdf_count": len(pdfs),
        "extracted_count": len(extracted),
        "pdfs": pdfs,
        "extracted": extracted,
        "manifest": _read_json(manifest) if manifest.exists() else None,
    }


@router.get("/assets/graph")
def assets_graph(request: Request):
    from fastapi.responses import HTMLResponse

    ws = _ws(request)
    for name in ("knowledge_graph.html", "graph.html"):
        path = ws / "literature" / name
        if path.is_file():
            return HTMLResponse(path.read_text(encoding="utf-8"))
    raise HTTPException(status_code=404, detail="missing file: knowledge_graph.html")


@router.get("/audit/events")
def audit_events(
    request: Request,
    action: str | None = None,
    agent: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    journal = _ws(request) / "audit" / "journal.jsonl"
    events: list[dict[str, Any]] = []
    if not journal.exists():
        return {"total": 0, "offset": offset, "limit": limit, "items": []}
    for line in journal.read_text(encoding="utf-8").strip().splitlines():
        if not line.strip():
            continue
        try:
            evt = json.loads(line)
        except Exception:
            logger.debug("skipping unparseable journal line", exc_info=True)
            continue
        if action and evt.get("action") != action.upper():
            continue
        if agent and evt.get("agent_or_tool") != agent:
            continue
        events.append(evt)
    # Newest first.
    events = events[::-1]
    return {
        "total": len(events),
        "offset": offset,
        "limit": limit,
        "items": events[offset : offset + limit],
    }


@router.get("/agents/actions")
def agent_actions(request: Request):
    ws = _ws(request)
    return actions_payload(workspace=str(ws))


# ---------------------------------------------------------------------------
# UI-07 presentation shapes (HCM-06 read side; GET only, never mutate).
#
# These routes serve the read-only presentation shapes of
# docs/architecture/research_ui/UI-07_PRESENTATION_SPEC.md §§1-6 over the
# workspace bound at app state. Discipline, per the spec binding rules:
#
# * R1/R2 — every reference is resolved server-side from the bound
#   workspace; query keys that smuggle caller-minted identities are refused
#   with 422 CALLER_IDENTITY_REFUSED (never bound, never trusted).
# * R4 — absent prerequisites are explicit `missing` entries with a reason,
#   never silent nulls or invented values.
# * R5 — pure reads: no writes, no manifest projection, no INDEX refresh, no
#   lock acquisition, no recover_partial, no identity minting (consumers call
#   require_recorded_identity only).
# * R6 — publication outputs are served ONLY with a CURRENT generation per
#   authority.generations.require_current_generation (reused, never
#   rewritten); any other status yields the typed currentness error, no bytes.
# ---------------------------------------------------------------------------


def _ui07_error(
    status_code: int, code: str, message: str, **details: Any
) -> HTTPException:
    """Typed UI-07 refusal: the code is machine-readable, the message human."""
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": details},
    )


def _ui07_refuse_caller_identity(request: Request) -> None:
    """Refuse caller-minted identities presented as authority (spec §5/§6(2)).

    The workspace/run/protocol/generation identity comes from the bound
    workspace only. Any query key naming such an identity is refused with
    422; the values are ignored, never bound.
    """
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


def _ui07_protocol_fingerprint(ws: Path) -> str | None:
    """Canonical protocol fingerprint, or None when it cannot be resolved.

    Reuses the protocol kit (never reimplemented); any failure yields None
    so the caller reports an explicit missing entry instead of inventing one.
    """
    try:
        from scholar_protocol.canonical import (
            canonical_fingerprint as _protocol_fingerprint,
        )
        from scholar_protocol.models import ResearchProtocol

        raw = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
        return _protocol_fingerprint(ResearchProtocol.model_validate(raw))
    except Exception:  # noqa: BLE001 - any failure is "unavailable", never fatal
        return None


def _ui07_sanitize_details(ws: Path, details: dict[str, Any]) -> dict[str, Any]:
    """Make gate details browser-safe: workspace-relative paths, JSON values."""
    clean: dict[str, Any] = {}
    for key, value in details.items():
        if isinstance(value, str) and (
            key.endswith("_path") or key == "generation_path"
        ):
            try:
                clean[key] = Path(value).relative_to(ws).as_posix()
            except ValueError:
                clean[key] = Path(value).name
        elif value is None or isinstance(value, (str, int, float, bool)):
            clean[key] = value
        elif isinstance(value, (list, dict)):
            clean[key] = value
        else:
            clean[key] = str(value)
    return clean


def _ui07_publication_status(ws: Path) -> dict[str, Any]:
    """The §3(e) status object, verbatim in every shape that carries it."""
    from scholar_harness.authority.generations import require_current_generation

    result = require_current_generation(ws)
    record = result.record
    generation_id: str | None = None
    if record is not None:
        generation_id = record.generation_id
    elif isinstance(result.details.get("generation_id"), str):
        generation_id = result.details["generation_id"]
    return {
        "shape": "ui07.publication-status-v1",
        "status": result.status.value,
        "code": result.code,
        "generation_id": generation_id,
        "outputs": dict(record.output_digests) if record is not None else {},
        "message": result.message,
        "details": _ui07_sanitize_details(ws, dict(result.details)),
    }


@router.get("/ui/project-summary")
def ui07_project_summary(request: Request):
    """§3(a): project summary + workflow readiness (explicit missing, never null-silence)."""
    _ui07_refuse_caller_identity(request)
    ws = _ws(request)

    missing: list[dict[str, Any]] = []

    try:
        from scholar_harness.workspace.identity import require_recorded_identity

        workspace_id: str | None = require_recorded_identity(ws)
    except Exception:  # noqa: BLE001 - unregistered workspaces report, never mint
        workspace_id = None
        missing.append({"file": "project.json", "reason": "IDENTITY_UNREGISTERED"})

    try:
        project_raw = json.loads((ws / "project.json").read_text(encoding="utf-8"))
        project_id = (
            project_raw.get("project_id") if isinstance(project_raw, dict) else None
        )
    except Exception:  # noqa: BLE001 - unreadable manifest is explicit, never fatal
        project_id = None
    if not isinstance(project_id, str) or not project_id:
        project_id = ws.name
        missing.append({"file": "project.json", "reason": "PROJECT_ID_ABSENT"})

    protocol_path = ws / "protocol.json"
    if protocol_path.is_file():
        protocol_fp = _ui07_protocol_fingerprint(ws)
        protocol = {"present": True, "fingerprint": protocol_fp}
        if protocol_fp is None:
            missing.append(
                {"file": "protocol.json", "reason": "PROTOCOL_FINGERPRINT_UNAVAILABLE"}
            )
    else:
        protocol = {"present": False, "fingerprint": None}
        missing.append({"file": "protocol.json", "reason": "NOT_PREPARED"})

    manifest_path = ws / "literature" / "screening" / "MANIFEST.json"
    run: dict[str, Any] | None = None
    batches_resolved = 0
    batch_total = 0
    all_batches_resolved = False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        run_id = (
            manifest.get("screening_run_id") if isinstance(manifest, dict) else None
        )
        rows = manifest.get("batches", []) if isinstance(manifest, dict) else []
    except Exception:  # noqa: BLE001 - absent/unreadable manifest is explicit
        run_id = None
        rows = None
    if isinstance(run_id, str) and run_id and isinstance(rows, list):
        batch_total = len(rows)
        for row in rows:
            if not isinstance(row, dict):
                continue
            try:
                idx = int(row.get("batch_index"))
            except (TypeError, ValueError):
                continue
            if (
                ws / "literature" / "screening" / f"batch_{idx:03d}_decisions.json"
            ).is_file():
                batches_resolved += 1
        run = {
            "screening_run_id": run_id,
            "batches": batch_total,
            "batches_resolved": batches_resolved,
        }
        all_batches_resolved = batch_total > 0 and batches_resolved == batch_total
        if batch_total == 0:
            missing.append(
                {"file": "literature/screening/MANIFEST.json", "reason": "NO_BATCHES"}
            )
    else:
        missing.append(
            {"file": "literature/screening/MANIFEST.json", "reason": "NOT_PREPARED"}
        )

    publication = _ui07_publication_status(ws)
    return {
        "shape": "ui07.project-summary-v1",
        "workspace_id": workspace_id,
        "project_id": project_id,
        "protocol": protocol,
        "run": run,
        "readiness": {
            "screening_prepared": run is not None,
            "all_batches_resolved": all_batches_resolved,
            "publication": publication,
        },
        "missing": missing,
    }


@router.get("/ui/publication-status")
def ui07_publication_status(request: Request):
    """§3(e): honest currentness for the screening publication (pure read)."""
    _ui07_refuse_caller_identity(request)
    return _ui07_publication_status(_ws(request))


@router.get("/ui/publication/outputs/{name}")
def ui07_publication_output(request: Request, name: str):
    """R6: one publication output, served ONLY with a CURRENT generation.

    Anything but CURRENT yields the typed currentness error (409) with the
    gate's message + details and no file bytes; unknown/traversal names are
    refused with 400 INVALID_FILE_NAME before currentness is even read.
    """
    from scholar_harness.authority.generations import (
        PUBLICATION_OUTPUTS,
        require_current_generation,
    )

    _ui07_refuse_caller_identity(request)
    if name not in PUBLICATION_OUTPUTS:
        raise _ui07_error(
            400,
            "INVALID_FILE_NAME",
            f"refusing request naming storage outside the served publication surface: {name!r}",
            requested=name,
            served_outputs=sorted(PUBLICATION_OUTPUTS),
        )
    ws = _ws(request)
    result = require_current_generation(ws)
    if result.status.value != "CURRENT":
        raise _ui07_error(
            409,
            result.code or "GENERATION_STALE",
            result.message,
            **_ui07_sanitize_details(ws, dict(result.details)),
        )
    path = ws / "literature" / name
    if not path.is_file():
        # Unreachable without a concurrent mutation (CURRENT verified the
        # digest), but fail-closed rather than serving nothing as success.
        raise _ui07_error(
            404,
            "BATCH_MISSING",
            f"missing file: literature/{name}",
            file=f"literature/{name}",
        )
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 - unreadable bytes are explicit
        raise _ui07_error(
            500,
            "UNPARSEABLE_JSON",
            f"cannot read publication output literature/{name} ({exc})",
            file=f"literature/{name}",
        ) from exc
    return {"filename": name, "content": content}
