"""PipelineSpec validation (HCM-03 neutral core).

Moved verbatim from ``console.api.pipelines``. Covers the invariant the CLI
executor relies on:

  - unique node ids, edges referencing existing nodes,
  - ``{{...}}`` template keys resolvable against ``settings`` (+ node outputs),
  - acyclic DAG with a well-defined topological execution order,
  - no two nodes writing the same output path.
"""

from __future__ import annotations

import re
from typing import Any

from .models import PipelineSpec

_TEMPLATE_RE = re.compile(r"\{\{\s*([A-Za-z0-9_.\/-]+)\s*\}\}")


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


def _output_collisions(spec: PipelineSpec) -> list[str]:
    owner: dict[str, str] = {}
    collisions: list[str] = []
    for n in spec.nodes:
        for out in n.outputs:
            if out in owner:
                collisions.append(f"{out!r} ({owner[out]} vs {n.id})")
            owner[out] = n.id
    return collisions
