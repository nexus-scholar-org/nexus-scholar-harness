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
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, field_validator

from .audit import log_event

router = APIRouter(prefix="/api/v1/pipelines", tags=["pipelines"])

SCHEMA_VERSION = "0.1.0"
_TEMPLATE_RE = re.compile(r"\{\{\s*([A-Za-z0-9_.\/-]+)\s*\}\}")


class PipelineNode(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    kit: str
    command: list[str]
    args: dict[str, Any] = {}
    inputs: list[str] = []
    outputs: list[str] = []
    on_fail: Literal["abort", "skip", "continue"] = "abort"
    requires_decision: bool = False


class PipelineSpec(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str = SCHEMA_VERSION
    id: str
    archetype: str = "PRISMA_SLR"
    name: str = ""
    workspace_slug: str = ""
    settings: dict[str, Any] = {}
    nodes: list[PipelineNode]
    edges: list[list[str]] = []
    dry_run: dict[str, Any] = {}
    created_by: str = "console"
    fingerprint: str = ""

    @field_validator("schema_version")
    @classmethod
    def _schema_version(cls, v: str) -> str:
        if v != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version {v!r}; expected {SCHEMA_VERSION!r}")
        return v

    @field_validator("edges")
    @classmethod
    def _edge_shape(cls, v: list[list[str]]) -> list[list[str]]:
        for edge in v:
            if not isinstance(edge, list) or len(edge) != 2 or not all(isinstance(x, str) and x for x in edge):
                raise ValueError(f"edges must be [from_id, to_id] pairs, got {edge!r}")
        return v


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


def _lookup(key: str, settings: dict[str, Any], slot_keys: set[str]) -> bool:
    """True if `key` resolves against settings/slots (dotted paths included)."""
    if key in slot_keys:
        return True
    node = settings
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return True


def _extract_template_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, str):
        keys.update(m.group(1) for m in _TEMPLATE_RE.finditer(value))
    elif isinstance(value, list):
        for item in value:
            keys.update(_extract_template_keys(item))
    elif isinstance(value, dict):
        for item in value.values():
            keys.update(_extract_template_keys(item))
    return keys


def _toposort(node_ids: set[str], edges: list[list[str]]) -> tuple[list[str], list[str]]:
    """Kahn's algorithm. Returns (order, cycle_errors)."""
    indegree = {nid: 0 for nid in node_ids}
    adj: dict[str, list[str]] = {nid: [] for nid in node_ids}
    for src, dst in edges:
        if dst in indegree:
            indegree[dst] += 1
        adj[src].append(dst)
    ready = [nid for nid in node_ids if indegree[nid] == 0]
    order: list[str] = []
    while ready:
        node = ready.pop()
        order.append(node)
        for nxt in adj[node]:
            if nxt in indegree:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    ready.append(nxt)
    errors: list[str] = []
    if len(order) != len(node_ids):
        cyclic = sorted(nid for nid in node_ids if indegree[nid] > 0)
        errors.append(f"DAG contains a cycle involving nodes: {cyclic}")
    return order, errors


def validate_spec(spec: PipelineSpec) -> dict[str, Any]:
    """Structural + semantic validation. Returns {errors: [...], warnings: [...]}."""
    errors: list[str] = []
    warnings: list[str] = []

    node_ids = [n.id for n in spec.nodes]
    if not node_ids:
        errors.append("spec must contain at least one node")
    dups = sorted({nid for nid in node_ids if node_ids.count(nid) > 1})
    if dups:
        errors.append(f"duplicate node ids: {dups}")

    id_set = set(node_ids)
    for src, dst in spec.edges:
        if src not in id_set:
            errors.append(f"edge references unknown source node {src!r}")
        if dst not in id_set:
            errors.append(f"edge references unknown target node {dst!r}")

    slot_keys = {"workspace_slug", "rq_id", "per_node_limit"}
    # Node-output references resolve at runtime: {{node_id.output_path}}.
    output_refs = {f"{n.id}.{out}" for n in spec.nodes for out in n.outputs}
    for n in spec.nodes:
        if not n.command:
            errors.append(f"node {n.id}: command must not be empty")
        unresolved = {k for k in _extract_template_keys(n.args)
                      if not _lookup(k, spec.settings, slot_keys) and k not in output_refs}
        if unresolved:
            errors.append(f"node {n.id}: unresolved template keys {sorted(unresolved)}")

    order, cycle_errors = _toposort(id_set, spec.edges)
    errors.extend(cycle_errors)

    output_owner: dict[str, str] = {}
    for n in spec.nodes:
        for out in n.outputs:
            if out in output_owner:
                errors.append(f"output path collision: {out!r} written by both {output_owner[out]} and {n.id}")
            output_owner[out] = n.id

    return {"errors": errors, "warnings": warnings, "order": order if not cycle_errors else []}


# ---------------------------------------------------------------------------
# fingerprint
# ---------------------------------------------------------------------------

def _fingerprint(spec: PipelineSpec) -> str:
    data = spec.model_dump()
    data.pop("fingerprint", None)

    def _sort(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: _sort(v) for k, v in sorted(value.items())}
        if isinstance(value, list):
            return [_sort(v) for v in value]
        return value

    canonical = json.dumps(_sort(data), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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
    if allow_builtin and spec_id == PRISMA_SLR_DEFAULT["id"]:
        return PipelineSpec.model_validate(PRISMA_SLR_DEFAULT)
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
    if PRISMA_SLR_DEFAULT["id"] not in saved:
        saved.insert(0, PRISMA_SLR_DEFAULT["id"])
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


def _output_collisions(spec: PipelineSpec) -> list[str]:
    owner: dict[str, str] = {}
    collisions: list[str] = []
    for n in spec.nodes:
        for out in n.outputs:
            if out in owner:
                collisions.append(f"{out!r} ({owner[out]} vs {n.id})")
            owner[out] = n.id
    return collisions