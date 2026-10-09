"""PipelineSpec CRUD + dry-run (SPECS §3, §4, §8; M5.4 prerequisite).

PipelineSpec (`schema_version 0.1.0`) is pure data: the console editor stores
and validates it, the CLI executor (M5.4) will consume the identical file.
Storage is the runtime dir `<workspace>/.harness-console/pipelines/{id}.json`
(never committed). The built-in `prisma_slr_default` template is available for
read/browse even before any spec is saved.

Validation covers the invariant that the CLI executor relies on:
  - unique node ids, edges referencing existing nodes,
  - `{{...}}` template keys resolvable against `settings` (+ node outputs),
  - acyclic DAG with a well-defined topological execution order,
  - no two nodes writing the same output path.

`dry-run` validates and resolves everything in memory — it never touches any
canonical workspace file (SPECS acceptance: `test_pipeline_dry_run_writes_nothing`).

Models, validation, topological scheduling, and fingerprinting live in the
neutral ``scholar_harness.pipeline`` core (HCM-03) and are re-exported here
so existing seams keep working. This module retains only transport-owned
concerns: HTTP endpoints, the `.harness-console` spec store, and the
built-in gallery templates.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict

from ...pipeline import (
    _TEMPLATE_RE,
    SCHEMA_VERSION,
    PipelineNode,
    PipelineSpec,
    _extract_template_keys,
    _fingerprint,
    _lookup,
    _output_collisions,
    _toposort,
    validate_spec,
)
from .audit import log_event

# Re-exported neutral-core names (HCM-03): importing them from this module
# keeps working, but new code should import from `scholar_harness.pipeline`.
__all__ = [
    "BUILTIN_TEMPLATES",
    "PipelineNode",
    "PipelineSpec",
    "SCHEMA_VERSION",
    "_TEMPLATE_RE",
    "_extract_template_keys",
    "_fingerprint",
    "_lookup",
    "_output_collisions",
    "_toposort",
    "router",
    "store_path",
    "validate_spec",
]

router = APIRouter(prefix="/api/v1/pipelines", tags=["pipelines"])


# ---------------------------------------------------------------------------
# validation helpers
# ---------------------------------------------------------------------------

PRISMA_SLR_DEFAULT = {
    "schema_version": SCHEMA_VERSION,
    "id": "prisma_slr_default",
    "archetype": "PRISMA_SLR",
    "name": "PRISMA SLR (2020) - default",
    "workspace_slug": "my-review",
    "settings": {
        "rq_ids": ["RQ1", "RQ2"],
        "queries": {"rq1_query": "multispectral UAV weed segmentation"},
        "provider_priority": ["openalex", "semantic_scholar", "arxiv"],
    },
    "nodes": [
        {
            "id": "n1_discovery",
            "kit": "scholar-search-kit",
            "command": ["scholar-search", "run"],
            "args": {"query": "{{queries.rq1_query}}", "providers": "{{provider_priority}}", "year_min": 2019, "limit": 2000},
            "inputs": [],
            "outputs": ["literature/candidates.json"],
            "on_fail": "abort",
        },
        {
            "id": "n2_dedup",
            "kit": "scholar-search-kit",
            "command": ["scholar-search", "dedup"],
            "args": {"input": "{{n1_discovery.literature/candidates.json}}"},
            "inputs": ["literature/candidates.json"],
            "outputs": ["literature/corpus.json"],
            "on_fail": "abort",
        },
        {
            "id": "n3_screen",
            "kit": "harness-agent-screen",
            "command": ["python", "src/scholar_harness/agent_screen.py", "prepare"],
            "args": {"workspace": "{{workspace_slug}}"},
            "inputs": ["literature/corpus.json"],
            "outputs": ["literature/screening/batch_*.json"],
            "on_fail": "abort",
            "requires_decision": True,
        },
    ],
    "edges": [["n1_discovery", "n2_dedup"], ["n2_dedup", "n3_screen"]],
    "dry_run": {"per_node_limit": 25},
    "created_by": "console",
    "fingerprint": "",
}

# The five canonical review playbook archetypes (inception.ALL_PLAYBOOKS) each
# ship a 1-click template so the gallery covers every research paradigm:
#   PRISMA_SLR          -> complete systematic SLR (default)
#   SCOPING_REVIEW      -> JBI-style evidence map (broad search, charting stop)
#   RAPID_EVIDENCE      -> REA guidelines: narrow, recent, prioritized provider
#   DESIGN_SCIENCE      -> Hevner DSR: artifact-oriented pipeline + eval matrix
#   STUDENT_DISSERTATION-> APA/JBI-adapted: two-wave studio review
# Templates are scaffolds: the same {{settings}}/node-output template language
# and validation invariants as user specs, so dry-run/export/run work unchanged.

SCOPING_REVIEW_DEFAULT: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "id": "scoping_review_default",
    "archetype": "SCOPING_REVIEW",
    "name": "Scoping Review (JBI) - breadth-first evidence map",
    "workspace_slug": "my-scoping-review",
    "settings": {
        "rq_ids": ["RQ1"],
        "queries": {"rq1_query": "stakeholder perception urban green space UAV monitoring"},
        "provider_priority": ["openalex", "semantic_scholar", "arxiv", "pubmed"],
    },
    "nodes": [
        {
            "id": "n1_scope_discovery",
            "kit": "scholar-search-kit",
            "command": ["scholar-search", "run"],
            "args": {"query": "{{queries.rq1_query}}", "providers": "{{provider_priority}}", "year_min": 2010, "limit": 5000},
            "inputs": [],
            "outputs": ["literature/candidates.json"],
            "on_fail": "abort",
        },
        {
            "id": "n2_dedup",
            "kit": "scholar-search-kit",
            "command": ["scholar-search", "dedup"],
            "args": {"input": "{{n1_scope_discovery.literature/candidates.json}}"},
            "inputs": ["literature/candidates.json"],
            "outputs": ["literature/corpus.json"],
            "on_fail": "abort",
        },
        {
            "id": "n3_scope_screen",
            "kit": "harness-agent-screen",
            "command": ["python", "src/scholar_harness/agent_screen.py", "prepare"],
            "args": {"workspace": "{{workspace_slug}}"},
            "inputs": ["literature/corpus.json"],
            "outputs": ["literature/screening/batch_*.json"],
            "on_fail": "abort",
            "requires_decision": True,
        },
    ],
    "edges": [["n1_scope_discovery", "n2_dedup"], ["n2_dedup", "n3_scope_screen"]],
    "dry_run": {"per_node_limit": 25},
    "created_by": "console",
    "fingerprint": "",
}

RAPID_EVIDENCE_DEFAULT: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "id": "rapid_evidence_default",
    "archetype": "RAPID_EVIDENCE",
    "name": "Rapid Evidence Assessment (REA) - recent prioritized match",
    "workspace_slug": "my-rapid-evidence",
    "settings": {
        "rq_ids": ["RQ1"],
        "queries": {"rq1_query": "risk of bias assessment tool screening efficiency"},
        "provider_priority": "openalex",
    },
    "nodes": [
        {
            "id": "n1_rapid_discovery",
            "kit": "scholar-search-kit",
            "command": ["scholar-search", "run"],
            "args": {"query": "{{queries.rq1_query}}", "providers": "{{provider_priority}}", "year_min": 2020, "limit": 800},
            "inputs": [],
            "outputs": ["literature/candidates.json"],
            "on_fail": "abort",
        },
        {
            "id": "n2_dedup",
            "kit": "scholar-search-kit",
            "command": ["scholar-search", "dedup"],
            "args": {"input": "{{n1_rapid_discovery.literature/candidates.json}}"},
            "inputs": ["literature/candidates.json"],
            "outputs": ["literature/corpus.json"],
            "on_fail": "abort",
        },
        {
            "id": "n3_rapid_screen",
            "kit": "harness-agent-screen",
            "command": ["python", "src/scholar_harness/agent_screen.py", "prepare"],
            "args": {"workspace": "{{workspace_slug}}"},
            "inputs": ["literature/corpus.json"],
            "outputs": ["literature/screening/batch_*.json"],
            "on_fail": "abort",
            "requires_decision": True,
        },
        {
            "id": "n4_fulltext",
            "kit": "scholar-pdf-kit",
            "command": ["scholar-pdf", "download"],
            "args": {"input": "literature/included.json", "output": "pdfs/", "max-concurrent": 10, "strict-validate": True},
            "inputs": ["literature/included.json"],
            "outputs": ["pdfs/**"],
            "on_fail": "abort",
        },
    ],
    "edges": [
        ["n1_rapid_discovery", "n2_dedup"],
        ["n2_dedup", "n3_rapid_screen"],
        ["n3_rapid_screen", "n4_fulltext"],
    ],
    "dry_run": {"per_node_limit": 25},
    "created_by": "console",
    "fingerprint": "",
}

DESIGN_SCIENCE_DEFAULT: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "id": "design_science_default",
    "archetype": "DESIGN_SCIENCE",
    "name": "Design Science (Hevner DSR) - artifact evaluation pipeline",
    "workspace_slug": "my-design-science",
    "settings": {
        "rq_ids": ["RQ1", "RQ2"],
        "queries": {"design_query": "multispectral UAV weed segmentation artifact evaluation benchmark"},
        "provider_priority": ["openalex", "semantic_scholar", "arxiv"],
    },
    "nodes": [
        {
            "id": "n1_ds_discovery",
            "kit": "scholar-search-kit",
            "command": ["scholar-search", "run"],
            "args": {"query": "{{queries.design_query}}", "providers": "{{provider_priority}}", "year_min": 2018, "limit": 3000},
            "inputs": [],
            "outputs": ["literature/candidates.json"],
            "on_fail": "abort",
        },
        {
            "id": "n2_dedup",
            "kit": "scholar-search-kit",
            "command": ["scholar-search", "dedup"],
            "args": {"input": "{{n1_ds_discovery.literature/candidates.json}}"},
            "inputs": ["literature/candidates.json"],
            "outputs": ["literature/corpus.json"],
            "on_fail": "abort",
        },
        {
            "id": "n3_ds_screen",
            "kit": "harness-agent-screen",
            "command": ["python", "src/scholar_harness/agent_screen.py", "prepare"],
            "args": {"workspace": "{{workspace_slug}}"},
            "inputs": ["literature/corpus.json"],
            "outputs": ["literature/screening/batch_*.json"],
            "on_fail": "abort",
            "requires_decision": True,
        },
        {
            "id": "n4_ds_artifacts",
            "kit": "scholar-pdf-kit",
            "command": ["scholar-pdf", "download"],
            "args": {"input": "literature/corpus.json", "output": "pdfs/", "smart-names": True},
            "inputs": ["literature/corpus.json"],
            "outputs": ["pdfs/**"],
            "on_fail": "abort",
        },
        {
            "id": "n5_ds_matrix",
            "kit": "scholar-rag-kit",
            "command": ["scholar-rag", "matrix"],
            "args": {"protocol": "protocol.json", "db-path": "rag/chroma_db", "output-dir": "literature"},
            "inputs": [],
            "outputs": ["literature/synthesis_matrix.md"],
            "on_fail": "continue",
        },
    ],
    "edges": [
        ["n1_ds_discovery", "n2_dedup"],
        ["n2_dedup", "n3_ds_screen"],
        ["n3_ds_screen", "n4_ds_artifacts"],
        ["n3_ds_screen", "n5_ds_matrix"],
    ],
    "dry_run": {"per_node_limit": 25},
    "created_by": "console",
    "fingerprint": "",
}

STUDENT_DISSERTATION_DEFAULT: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "id": "student_dissertation_default",
    "archetype": "STUDENT_DISSERTATION",
    "name": "Student Dissertation (APA/JBI adapted) - two-wave studio review",
    "workspace_slug": "my-dissertation",
    "settings": {
        "rq_ids": ["RQ1", "RQ2"],
        "queries": {"rq1_query": "unmanned aerial vehicles precision agriculture weed detection"},
        "provider_priority": ["openalex", "semantic_scholar", "arxiv", "pubmed", "crossref"],
    },
    "nodes": [
        {
            "id": "n1_thesis_discovery",
            "kit": "scholar-search-kit",
            "command": ["scholar-search", "run"],
            "args": {"query": "{{queries.rq1_query}}", "providers": "{{provider_priority}}", "year_min": 2015, "limit": 4000},
            "inputs": [],
            "outputs": ["literature/candidates.json"],
            "on_fail": "abort",
        },
        {
            "id": "n2_dedup",
            "kit": "scholar-search-kit",
            "command": ["scholar-search", "dedup"],
            "args": {"input": "{{n1_thesis_discovery.literature/candidates.json}}"},
            "inputs": ["literature/candidates.json"],
            "outputs": ["literature/corpus.json"],
            "on_fail": "abort",
        },
        {
            "id": "n3_thesis_screen",
            "kit": "harness-agent-screen",
            "command": ["python", "src/scholar_harness/agent_screen.py", "prepare"],
            "args": {"workspace": "{{workspace_slug}}"},
            "inputs": ["literature/corpus.json"],
            "outputs": ["literature/screening/batch_*.json"],
            "on_fail": "abort",
            "requires_decision": True,
        },
        {
            "id": "n4_thesis_fulltext",
            "kit": "scholar-pdf-kit",
            "command": ["scholar-pdf", "download"],
            "args": {"input": "literature/included.json", "output": "pdfs/", "strict-validate": True},
            "inputs": ["literature/included.json"],
            "outputs": ["pdfs/**"],
            "on_fail": "abort",
        },
    ],
    "edges": [
        ["n1_thesis_discovery", "n2_dedup"],
        ["n2_dedup", "n3_thesis_screen"],
        ["n3_thesis_screen", "n4_thesis_fulltext"],
    ],
    "dry_run": {"per_node_limit": 25},
    "created_by": "console",
    "fingerprint": "",
}

BUILTIN_TEMPLATES: dict[str, dict[str, Any]] = {
    PRISMA_SLR_DEFAULT["id"]: PRISMA_SLR_DEFAULT,
    SCOPING_REVIEW_DEFAULT["id"]: SCOPING_REVIEW_DEFAULT,
    RAPID_EVIDENCE_DEFAULT["id"]: RAPID_EVIDENCE_DEFAULT,
    DESIGN_SCIENCE_DEFAULT["id"]: DESIGN_SCIENCE_DEFAULT,
    STUDENT_DISSERTATION_DEFAULT["id"]: STUDENT_DISSERTATION_DEFAULT,
}


# Validation, topological scheduling, and fingerprinting are owned by the
# neutral core (scholar_harness.pipeline, re-exported above).


# ---------------------------------------------------------------------------
# storage
# ---------------------------------------------------------------------------

def _store(ws: Path) -> Path:
    d = ws / ".harness-console" / "pipelines"
    d.mkdir(parents=True, exist_ok=True)
    return d


def store_path(ws: Path) -> Path:
    """Runtime store dir for pipeline specs (also used by the job runner)."""
    return _store(ws)


def _load_spec(ws: Path, spec_id: str, allow_builtin: bool = True) -> PipelineSpec:
    path = _store(ws) / f"{spec_id}.json"
    if path.is_file():
        try:
            return PipelineSpec.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"unparseable pipeline spec {spec_id}: {exc}") from exc
    if allow_builtin and spec_id in BUILTIN_TEMPLATES:
        return PipelineSpec.model_validate(BUILTIN_TEMPLATES[spec_id])
    raise HTTPException(status_code=404, detail=f"missing pipeline spec: {spec_id}")


def _write_spec(ws: Path, spec: PipelineSpec) -> PipelineSpec:
    spec.fingerprint = _fingerprint(spec)
    path = _store(ws) / f"{spec.id}.json"
    tmp = path.with_name(path.name + f".tmp-{uuid.uuid4().hex[:8]}")
    tmp.write_text(json.dumps(spec.model_dump(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return spec


# ---------------------------------------------------------------------------
# endpoints
# ---------------------------------------------------------------------------

@router.get("")
def list_pipelines(request: Request) -> dict[str, Any]:
    ws: Path = request.app.state.workspace
    saved = sorted(p.name[: -len(".json")] for p in _store(ws).glob("*.json") if p.is_file())
    builtin_ids = list(BUILTIN_TEMPLATES)
    saved = [bid for bid in builtin_ids if bid not in saved] + saved
    return {"count": len(saved), "ids": saved}


@router.get("/{spec_id}/export")
def export_pipeline_script(request: Request, spec_id: str, script_format: str = "sh") -> Response:
    """Render a saved PipelineSpec into an equivalently-executing bash script.

    The exported script mirrors `uv run scholar-harness run --pipeline <spec>`
    for the same workspace (topo order, resolved args, idempotency guard,
    on_fail, requires_decision halt). Lazy import avoids a cycle with the
    integrations renderer.
    """
    from scholar_harness.integrations.pipeline_script import render_pipeline_sh

    if script_format != "sh":
        raise HTTPException(status_code=400, detail="unsupported export format: only 'sh'")
    ws: Path = request.app.state.workspace
    spec = _load_spec(ws, spec_id)
    script = render_pipeline_sh(spec, ws)
    return Response(
        content=script,
        media_type="text/x-shellscript",
        headers={"Content-Disposition": f'attachment; filename="{spec.id}.sh"'},
    )


class NewSpecBody(BaseModel):
    model_config = ConfigDict(extra="ignore")

    spec: dict[str, Any]


@router.post("", status_code=201)
def post_pipeline(body: NewSpecBody, request: Request) -> dict[str, Any]:
    ws: Path = request.app.state.workspace
    raw: dict[str, Any] = dict(body.spec)
    raw.pop("fingerprint", None)
    try:
        spec = PipelineSpec.model_validate(raw)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"invalid PipelineSpec: {exc}") from exc

    result = validate_spec(spec)
    if result["errors"]:
        raise HTTPException(status_code=422, detail={"errors": result["errors"], "warnings": result["warnings"]})

    spec = _write_spec(ws, spec)
    log_event(
        workspace=ws,
        action="PIPELINE_UPSERT",
        description=f"Saved pipeline spec {spec.id} (fingerprint {spec.fingerprint[:24]}…)",
        inputs=[],
        outputs=[f".harness-console/pipelines/{spec.id}.json"],
        parameters={"spec_id": spec.id, "nodes": len(spec.nodes), "edges": len(spec.edges)},
        refresh_index=False,
    )
    return {"spec": spec.model_dump()}


@router.get("/{spec_id}")
def get_pipeline(request: Request, spec_id: str) -> dict[str, Any]:
    ws: Path = request.app.state.workspace
    spec = _load_spec(ws, spec_id)
    return {"spec": spec.model_dump()}


class DryRunBody(BaseModel):
    per_node_limit: int | None = None
    workspace_slug: str | None = None


@router.post("/{spec_id}/dry-run")
def dry_run_pipeline(body: DryRunBody | None, spec_id: str, request: Request) -> dict[str, Any]:
    ws: Path = request.app.state.workspace
    spec = _load_spec(ws, spec_id)
    if body and body.workspace_slug:
        spec.workspace_slug = body.workspace_slug

    result = validate_spec(spec)
    errors = list(result["errors"])
    per_node_limit = body.per_node_limit if body and body.per_node_limit else spec.dry_run.get("per_node_limit", 25)

    if errors:
        return {
            "id": spec.id,
            "valid": False,
            "errors": errors,
            "warnings": result["warnings"],
            "nodes_ordered": [],
            "requires_decision": [],
            "output_collisions": [],
            "per_node_limit": per_node_limit,
            "message": "dry-run rejected: spec is not valid",
        }

    collisions = _output_collisions(spec)
    if collisions:
        errors.append(f"output path collisions: {collisions}")

    return {
        "id": spec.id,
        "valid": not errors,
        "errors": errors,
        "warnings": result["warnings"],
        "nodes_ordered": result["order"],
        "requires_decision": [n.id for n in spec.nodes if n.requires_decision],
        "output_collisions": collisions,
        "per_node_limit": per_node_limit,
        "message": f"dry-run OK: {len(result['order'])} nodes would run, limit {per_node_limit} per node, no canonical files modified",
    }