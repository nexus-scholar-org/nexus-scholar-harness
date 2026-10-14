"""Read-only endpoints over the canonical workspace contract (SPECS section 3).

Every response returns canonical file contents (or a 404 listing the missing
relative path). No console-owned state is involved: these are thin views over
the same files agents read.
"""

from __future__ import annotations

import json
import logging
import re
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


# ---------------------------------------------------------------------------
# UI-05 evidence lineage (GET only, never mutate).
#
# One read-only trace view: given a claim id or a chunk id, the server
# assembles claim -> chunk(s) -> extracted document -> study -> screening
# decision from the workspace bound at app state. Every join is resolved
# here, from recorded Contract v1 artifacts through the frozen models
# (reused, never rewritten):
#
# * claims_ledger       (claims with evidence ids + citation tokens, and the
#                        evidence itself: quote, locator, document link)
# * document_manifest   (document records: study link, source hash, status)
# * corpus_snapshot     (studies: canonical ids, recorded aliases, titles)
# * screening_decisions (recorded decisions with reasons)
# * artifact_registry   (which payload is the accepted one per type)
#
# Discipline mirrors the UI-07 section above:
#
# * R1/R2 — claim_id/chunk_id are selectors resolved against the bound
#   workspace, never authority; any other caller-minted identity key is
#   refused with 422 CALLER_IDENTITY_REFUSED (never bound, never trusted).
# * R4 — a broken link is an explicit typed refusal (a per-leg `refusal`
#   with a stable code, or an HTTP typed error for entry-level failures),
#   never a silent null and never an invented value.
# * R5 — pure read: no writes, no registry mutation, no lock acquisition,
#   no recover_partial, no identity minting.
# * R6 — publication-linked traces serve ONLY with a CURRENT generation per
#   authority.generations.require_current_generation (reused, never
#   rewritten); any other status yields the typed currentness error, no bytes.
# * Joins span mixed identity eras (canonical STU- study ids beside legacy
#   SCI- aliases recorded on the corpus): a study resolves by canonical id
#   or by a recorded corpus alias only. A title, DOI, or filename never
#   binds a study; an unresolvable link refuses instead of guessing.
# * Entailment is never claimed: a verbatim quote is served as a quote, and
#   the claim verification axes are served exactly as stored (annotations,
#   never scores).
# ---------------------------------------------------------------------------


#: Frozen citation-token grammar ([rag:v2:workspace:study:chunk]); parsed, never minted.
_LINEAGE_CHUNK_TOKEN_RE = re.compile(r"\[rag:v2:([^:\]]+):([^:\]]+):([^:\]]+)\]")


def _lineage_registry(ws: Path) -> dict[str, Any]:
    """The recorded artifact registry, or a typed refusal when it cannot be read."""
    path = ws / "audit" / "artifact_registry.json"
    if not path.is_file():
        raise _ui07_error(
            404,
            "LINEAGE_NOT_PREPARED",
            "no accepted Contract v1 artifact registry; no lineage can be assembled",
            file="audit/artifact_registry.json",
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - malformed canonical bytes are explicit
        raise _ui07_error(
            500,
            "UNPARSEABLE_JSON",
            f"unparseable JSON: artifact_registry.json ({exc})",
            file="artifact_registry.json",
        ) from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("artifacts"), dict):
        raise _ui07_error(
            500,
            "LINEAGE_REGISTRY_INVALID",
            "artifact_registry.json carries no artifacts mapping",
            file="audit/artifact_registry.json",
        )
    return payload


def _lineage_newest(registry: dict[str, Any], artifact_type: str) -> dict[str, Any]:
    """The newest accepted registry entry of one type, or a typed 404.

    Newest means the largest accepted_at string; ISO-8601 stamps order
    lexicographically, so no clock is read and no timestamp is reformatted.
    """
    candidates = [
        (artifact_id, entry)
        for artifact_id, entry in registry["artifacts"].items()
        if isinstance(entry, dict) and entry.get("artifact_type") == artifact_type
    ]
    if not candidates:
        raise _ui07_error(
            404,
            "LINEAGE_NOT_PREPARED",
            f"no accepted {artifact_type} artifact; no lineage can be assembled",
            artifact_type=artifact_type,
        )

    def _stamp(item: tuple[str, dict[str, Any]]) -> str:
        accepted_at = item[1].get("accepted_at")
        return accepted_at if isinstance(accepted_at, str) else ""

    artifact_id, entry = sorted(candidates, key=_stamp)[-1]
    return {"artifact_id": artifact_id, **entry}


def _lineage_load(
    ws: Path, entry: dict[str, Any], *, kind: str, invalid_code: str
) -> dict[str, Any]:
    """Load one registered payload and check it against its recorded hash.

    A recorded hash that disagrees with the payload on disk is a compromised
    registry, not a missing file: it refuses instead of serving the bytes.
    """
    from scholar_harness.contracts.canonical import canonical_fingerprint

    rel = entry.get("path")
    if not isinstance(rel, str) or not rel:
        raise _ui07_error(
            500,
            "LINEAGE_REGISTRY_INVALID",
            f"registry entry {entry.get('artifact_id')!r} carries no path",
            artifact_type=kind,
        )
    path = (ws / rel).resolve() if isinstance(rel, str) else ws
    try:
        path.relative_to(ws)
    except ValueError as exc:
        raise _ui07_error(
            500,
            "LINEAGE_REGISTRY_INVALID",
            f"registry path {rel!r} resolves outside the workspace",
            artifact_type=kind,
        ) from exc
    if not path.is_file():
        raise _ui07_error(
            404,
            "LINEAGE_NOT_PREPARED",
            f"registered {kind} payload is absent on disk: {rel}",
            file=rel,
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - malformed canonical bytes are explicit
        raise _ui07_error(
            500,
            "UNPARSEABLE_JSON",
            f"unparseable JSON: {rel} ({exc})",
            file=rel,
        ) from exc
    if not isinstance(payload, dict):
        raise _ui07_error(
            500, invalid_code, f"registered {kind} payload is not a JSON object"
        )
    recorded = entry.get("sha256")
    try:
        actual = canonical_fingerprint(payload)
    except Exception as exc:  # noqa: BLE001 - an unhashable payload is explicit
        raise _ui07_error(
            500, invalid_code, f"registered {kind} payload cannot be hashed ({exc})"
        ) from exc
    if not isinstance(recorded, str) or recorded != actual:
        raise _ui07_error(
            500,
            "LINEAGE_REGISTRY_INVALID",
            f"registered {kind} payload differs from its registry hash",
            artifact_type=kind,
        )
    return payload


def _lineage_chunk_ids(token: str) -> tuple[str, str] | None:
    """Split one citation token into (study segment, chunk segment), or None."""
    match = _LINEAGE_CHUNK_TOKEN_RE.fullmatch(token.strip())
    if match is None:
        return None
    return match.group(2), match.group(3)


@router.get("/ui/lineage")
def ui05_lineage(
    request: Request, claim_id: str | None = None, chunk_id: str | None = None
):
    """Assemble one evidence lineage trace (claim/chunk -> decision).

    Exactly one of `claim_id`/`chunk_id` selects the trace; both are
    selectors resolved against the bound workspace, never authority. Every
    served string comes from a recorded payload validated through its
    frozen Contract model; every broken link refuses with a stable code.
    """
    from scholar_harness.authority.generations import require_current_generation
    from scholar_harness.contracts.models import (
        ClaimEvidenceLedger,
        CorpusSnapshotArtifact,
        DocumentManifestArtifact,
        ScreeningDecisionsArtifact,
    )
    from scholar_harness.workspace.identity import require_recorded_identity

    _ui07_refuse_caller_identity(request)
    want_claim = claim_id.strip() if isinstance(claim_id, str) else ""
    want_chunk = chunk_id.strip() if isinstance(chunk_id, str) else ""
    if not want_claim and not want_chunk:
        raise _ui07_error(
            400,
            "MISSING_SELECTOR",
            "a lineage trace needs exactly one selector: claim_id or chunk_id",
            served_selectors=["claim_id", "chunk_id"],
        )
    if want_claim and want_chunk:
        raise _ui07_error(
            400,
            "CONFLICTING_SELECTOR",
            "a lineage trace takes one selector; claim_id and chunk_id were both given",
            served_selectors=["claim_id", "chunk_id"],
        )

    ws = _ws(request)
    current = require_current_generation(ws)
    if current.status.value != "CURRENT":
        raise _ui07_error(
            409,
            current.code or "GENERATION_STALE",
            current.message,
            **_ui07_sanitize_details(ws, dict(current.details)),
        )
    # Scope comes from the authorized generation record itself (verified
    # CURRENT above), never from a caller value and never minted here. When
    # the record is absent the recorded workspace identity is the fallback;
    # an unregistered workspace reports instead of minting.
    if current.record is not None:
        scope_workspace = current.record.workspace_id
    else:  # pragma: no cover - CURRENT always carries its record
        try:
            scope_workspace = require_recorded_identity(ws)
        except Exception as exc:  # noqa: BLE001 - unregistered workspaces report
            raise _ui07_error(
                409,
                "LINEAGE_IDENTITY_UNREGISTERED",
                "no recorded workspace identity, so lineage scope cannot be "
                f"confirmed ({exc})",
            ) from exc

    registry = _lineage_registry(ws)
    ledger_raw = _lineage_load(
        ws,
        _lineage_newest(registry, "claims_ledger"),
        kind="claims_ledger",
        invalid_code="LINEAGE_LEDGER_INVALID",
    )
    documents_raw = _lineage_load(
        ws,
        _lineage_newest(registry, "document_manifest"),
        kind="document_manifest",
        invalid_code="LINEAGE_DOCUMENTS_INVALID",
    )
    corpus_raw = _lineage_load(
        ws,
        _lineage_newest(registry, "corpus_snapshot"),
        kind="corpus_snapshot",
        invalid_code="LINEAGE_CORPUS_INVALID",
    )
    try:
        ledger = ClaimEvidenceLedger.model_validate(ledger_raw)
    except Exception as exc:  # noqa: BLE001 - a ledger that fails its schema is explicit
        raise _ui07_error(
            500, "LINEAGE_LEDGER_INVALID", f"claims ledger fails its schema ({exc})"
        ) from exc
    try:
        manifest = DocumentManifestArtifact.model_validate(documents_raw)
    except Exception as exc:  # noqa: BLE001
        raise _ui07_error(
            500,
            "LINEAGE_DOCUMENTS_INVALID",
            f"document manifest fails its schema ({exc})",
        ) from exc
    try:
        corpus = CorpusSnapshotArtifact.model_validate(corpus_raw)
    except Exception as exc:  # noqa: BLE001
        raise _ui07_error(
            500, "LINEAGE_CORPUS_INVALID", f"corpus snapshot fails its schema ({exc})"
        ) from exc

    triples = {
        ledger.artifact_id: (
            ledger.workspace_id,
            ledger.protocol_fingerprint,
            ledger.corpus_fingerprint,
        ),
        manifest.artifact_id: (
            manifest.workspace_id,
            manifest.protocol_fingerprint,
            manifest.corpus_fingerprint,
        ),
        corpus.artifact_id: (
            corpus.workspace_id,
            corpus.protocol_fingerprint,
            corpus.corpus_fingerprint,
        ),
    }
    if len(set(triples.values())) != 1:
        raise _ui07_error(
            409,
            "LINEAGE_GENERATION_MISMATCH",
            "lineage artifacts disagree on workspace/protocol/corpus parents; "
            "no single trace scope exists",
            artifact_ids=sorted(triples),
        )
    scope_triple = next(iter(triples.values()))

    # Decisions are pooled across every accepted screening_decisions artifact
    # of the trace scope: decisions are recorded per batch, so newest-only
    # would drop every batch but the last. Each candidate is hash-checked and
    # schema-validated like every other join input; only scope-matching ones
    # join, and an empty scope refuses instead of serving a partial chain.
    decision_entries = [
        (artifact_id, entry)
        for artifact_id, entry in registry["artifacts"].items()
        if isinstance(entry, dict)
        and entry.get("artifact_type") == "screening_decisions"
    ]
    if not decision_entries:
        raise _ui07_error(
            404,
            "LINEAGE_NOT_PREPARED",
            "no accepted screening_decisions artifact; no lineage can be assembled",
            artifact_type="screening_decisions",
        )
    pooled: list[Any] = []
    for artifact_id, entry in sorted(decision_entries):
        candidate_raw = _lineage_load(
            ws,
            {"artifact_id": artifact_id, **entry},
            kind="screening_decisions",
            invalid_code="LINEAGE_DECISIONS_INVALID",
        )
        try:
            candidate = ScreeningDecisionsArtifact.model_validate(candidate_raw)
        except Exception as exc:  # noqa: BLE001
            raise _ui07_error(
                500,
                "LINEAGE_DECISIONS_INVALID",
                f"screening decisions fail their schema ({exc})",
            ) from exc
        if (
            candidate.workspace_id,
            candidate.protocol_fingerprint,
            candidate.corpus_fingerprint,
        ) == scope_triple:
            pooled.append(candidate)
    if not pooled:
        raise _ui07_error(
            409,
            "LINEAGE_GENERATION_MISMATCH",
            "no accepted screening decisions share the ledger generation; "
            "no single trace scope exists",
            artifact_ids=sorted(a for a, _ in decision_entries),
        )
    (only_workspace, _, _) = next(iter(triples.values()))
    if only_workspace != scope_workspace:
        raise _ui07_error(
            409,
            "LINEAGE_GENERATION_MISMATCH",
            "lineage artifacts belong to a different workspace than the "
            "authorized generation",
            record_workspace_id=only_workspace,
        )

    if want_claim:
        selected = [c for c in ledger.data.claims if c.claim_id == want_claim]
        if not selected:
            raise _ui07_error(
                404,
                "CLAIM_MISSING",
                f"no recorded claim {want_claim!r} in the accepted ledger",
                claim_id=want_claim,
            )
    else:
        selected = [
            c
            for c in ledger.data.claims
            if any(
                (_lineage_chunk_ids(t) or ("", ""))[1] == want_chunk
                for t in c.citation_tokens
            )
        ]
        if not selected:
            raise _ui07_error(
                404,
                "CHUNK_MISSING",
                f"no recorded claim cites chunk {want_chunk!r}; refusing, never "
                "inventing a passage",
                chunk_id=want_chunk,
            )

    evidence_by_id = {e.evidence_id: e for e in ledger.data.evidence}
    documents_by_id = {d.document_id: d for d in manifest.data.documents}
    studies_by_id = {s.study_id: s for s in corpus.data.studies}
    alias_to_study: dict[str, str] = {}
    for study in corpus.data.studies:
        for alias in study.alias_ids:
            alias_to_study.setdefault(alias, study.study_id)

    def _resolve_study(study_id: str) -> Any | None:
        if study_id in studies_by_id:
            return studies_by_id[study_id]
        aliased = alias_to_study.get(study_id)
        if aliased is not None:
            return studies_by_id.get(aliased)
        return None

    def _resolve_decision(study_id: str) -> Any | None:
        canonical = study_id
        if canonical not in studies_by_id:
            aliased = alias_to_study.get(study_id)
            if aliased is not None:
                canonical = aliased
        matches = [
            d
            for artifact in pooled
            for d in artifact.data.decisions
            if d.study_id == canonical or alias_to_study.get(d.study_id) == canonical
        ]
        matches.sort(key=lambda d: d.decision_id)
        return matches[0] if matches else None

    claims_out: list[dict[str, Any]] = []
    complete = True
    for claim in sorted(selected, key=lambda c: c.claim_id):
        legs: list[dict[str, Any]] = []
        for evidence_id in claim.evidence_ids:
            evidence = evidence_by_id.get(evidence_id)
            if evidence is None:  # pragma: no cover - the frozen ledger model
                # already refuses dangling evidence ids, so this leg can only
                # fire on a payload that bypassed validation; it refuses here
                # rather than inventing a passage.
                complete = False
                legs.append(
                    {
                        "evidence": None,
                        "chunk_ids": [],
                        "document": None,
                        "study": None,
                        "decision": None,
                        "refusal": {
                            "code": "MISSING_CHUNK",
                            "message": (
                                f"claim {claim.claim_id} lists evidence "
                                f"{evidence_id!r} absent from the ledger; refusing, "
                                "never inventing a passage"
                            ),
                        },
                    }
                )
                continue
            leg_chunks = sorted(
                {
                    chunk
                    for token in claim.citation_tokens
                    if (parsed := _lineage_chunk_ids(token)) is not None
                    and parsed[0] == evidence.study_id
                    for chunk in [parsed[1]]
                }
            )
            document = documents_by_id.get(evidence.document_id)
            if document is None:
                complete = False
                legs.append(
                    {
                        "evidence": _evidence_out(evidence),
                        "chunk_ids": leg_chunks,
                        "document": None,
                        "study": None,
                        "decision": None,
                        "refusal": {
                            "code": "UNLINKED_DOCUMENT",
                            "message": (
                                f"evidence {evidence.evidence_id} names document "
                                f"{evidence.document_id!r} absent from the accepted "
                                "document manifest; refusing, never substituting "
                                "a neighbor document"
                            ),
                        },
                    }
                )
                continue
            if document.study_id != evidence.study_id:
                complete = False
                legs.append(
                    {
                        "evidence": _evidence_out(evidence),
                        "chunk_ids": leg_chunks,
                        "document": _document_out(document),
                        "study": None,
                        "decision": None,
                        "refusal": {
                            "code": "UNLINKED_DOCUMENT",
                            "message": (
                                f"evidence {evidence.evidence_id} names study "
                                f"{evidence.study_id!r} while its document "
                                f"{document.document_id} records study "
                                f"{document.study_id!r}; refusing, never "
                                "re-binding one study's text to another study"
                            ),
                        },
                    }
                )
                continue
            if document.source_hash != evidence.source_hash:
                complete = False
                legs.append(
                    {
                        "evidence": _evidence_out(evidence),
                        "chunk_ids": leg_chunks,
                        "document": _document_out(document),
                        "study": None,
                        "decision": None,
                        "refusal": {
                            "code": "UNLINKED_DOCUMENT",
                            "message": (
                                f"evidence {evidence.evidence_id} source hash "
                                "differs from its document's recorded source "
                                "hash; refusing, never quoting bytes the "
                                "manifest does not cover"
                            ),
                        },
                    }
                )
                continue
            if document.content_status.value not in ("VALID", "PARTIAL"):
                complete = False
                legs.append(
                    {
                        "evidence": _evidence_out(evidence),
                        "chunk_ids": leg_chunks,
                        "document": _document_out(document),
                        "study": None,
                        "decision": None,
                        "refusal": {
                            "code": "UNLINKED_DOCUMENT",
                            "message": (
                                f"document {document.document_id} content status "
                                f"is {document.content_status.value}; a passage "
                                "cannot be quoted from unusable bytes"
                            ),
                        },
                    }
                )
                continue
            study = _resolve_study(document.study_id)
            if study is None:
                complete = False
                legs.append(
                    {
                        "evidence": _evidence_out(evidence),
                        "chunk_ids": leg_chunks,
                        "document": _document_out(document),
                        "study": None,
                        "decision": None,
                        "refusal": {
                            "code": "UNKNOWN_STUDY",
                            "message": (
                                f"document {document.document_id} names study "
                                f"{document.study_id!r} absent from the accepted "
                                "corpus snapshot (canonical ids and recorded "
                                "aliases checked); refusing, never inferring a "
                                "study from a title, DOI, or filename"
                            ),
                        },
                    }
                )
                continue
            decision = _resolve_decision(study.study_id)
            if decision is None:
                complete = False
                legs.append(
                    {
                        "evidence": _evidence_out(evidence),
                        "chunk_ids": leg_chunks,
                        "document": _document_out(document),
                        "study": _study_out(study),
                        "decision": None,
                        "refusal": {
                            "code": "MISSING_DECISION",
                            "message": (
                                f"study {study.study_id} carries no recorded "
                                "screening decision in the accepted decisions "
                                "artifact; refusing, never defaulting a decision"
                            ),
                        },
                    }
                )
                continue
            legs.append(
                {
                    "evidence": _evidence_out(evidence),
                    "chunk_ids": leg_chunks,
                    "document": _document_out(document),
                    "study": _study_out(study),
                    "decision": {
                        "decision_id": decision.decision_id,
                        "study_id": decision.study_id,
                        "decision": decision.decision.value,
                        "reason": decision.reason,
                        "method": decision.method.value,
                        "screener_id": decision.screener_id,
                        "decided_at": decision.decided_at.isoformat(),
                    },
                    "refusal": None,
                }
            )
        claim_tokens = sorted(set(claim.citation_tokens))
        verification = (
            claim.verification.model_dump(mode="json")
            if claim.verification is not None
            else None
        )
        claims_out.append(
            {
                "claim_id": claim.claim_id,
                "claim_text": claim.claim_text,
                "claim_kind": claim.claim_kind,
                "study_ids": list(claim.study_ids),
                "evidence_ids": list(claim.evidence_ids),
                "citation_tokens": claim_tokens,
                "chunk_ids": sorted(
                    {
                        chunk
                        for token in claim_tokens
                        if (parsed := _lineage_chunk_ids(token)) is not None
                        for chunk in [parsed[1]]
                    }
                ),
                "verification": verification,
                "legs": legs,
            }
        )
    return {
        "shape": "ui07.lineage-trace-v1",
        "complete": complete,
        "selector": (
            {"claim_id": want_claim} if want_claim else {"chunk_id": want_chunk}
        ),
        "claims": claims_out,
        "publication": _ui07_publication_status(ws),
        "missing": [],
    }


def _evidence_out(evidence: Any) -> dict[str, Any]:
    """Serve one evidence record exactly as stored (quote and locator verbatim)."""
    return {
        "evidence_id": evidence.evidence_id,
        "quote": evidence.quote,
        "locator": evidence.locator,
        "study_id": evidence.study_id,
        "document_id": evidence.document_id,
        "source_hash": evidence.source_hash,
        "extraction_method": evidence.extraction_method.value,
    }


def _document_out(document: Any) -> dict[str, Any]:
    """Serve one document record exactly as stored."""
    return {
        "document_id": document.document_id,
        "study_id": document.study_id,
        "source_hash": document.source_hash,
        "content_status": document.content_status.value,
        "extracted_path": document.extracted_path,
        "extraction_method": document.extraction_method.value,
    }


def _study_out(study: Any) -> dict[str, Any]:
    """Serve one corpus study exactly as stored (aliases and locators verbatim)."""
    return {
        "study_id": study.study_id,
        "title": study.title,
        "alias_ids": list(study.alias_ids),
        "external_ids": {
            provider: list(values) for provider, values in study.external_ids.items()
        },
        "publication_year": study.publication_year,
    }
