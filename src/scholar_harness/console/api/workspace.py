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
        raise HTTPException(status_code=500, detail=f"unparseable JSON: {path.name}") from exc


def _list_dir(parent: Path, pattern: str, suffix: str | None = None) -> list[str]:
    if not parent.is_dir():
        return []
    out = sorted(str(p.name) for p in parent.glob(pattern))
    if suffix:
        out = [n for n in out if n.endswith(suffix)]
    return out


def _safe_join(root: Path, filename: str) -> Path:
    """Join a plain filename under root, rejecting any traversal."""
    if "/" in filename or "\\" in filename or ".." in filename or filename in ("", ".", ".."):
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
    return {"total": total, "offset": offset, "limit": limit, "items": docs[offset : offset + limit]}


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
    return {"count": len(_file_index(_ws(request) / "synthesis", SYNTHESIS_KINDS)), "files": _file_index(_ws(request) / "synthesis", SYNTHESIS_KINDS)}


@router.get("/phase4")
def phase4_index(request: Request):
    return {"count": len(_file_index(_ws(request) / "phase4", PHASE4_KINDS)), "files": _file_index(_ws(request) / "phase4", PHASE4_KINDS)}


@router.get("/synthesis/{filename}")
def synthesis_file(request: Request, filename: str):
    path = _safe_join(_ws(request) / "synthesis", filename)
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"missing file: synthesis/{filename}")
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
    return {"total": len(events), "offset": offset, "limit": limit, "items": events[offset : offset + limit]}


@router.get("/agents/actions")
def agent_actions(request: Request):
    ws = _ws(request)
    return actions_payload(workspace=str(ws))
