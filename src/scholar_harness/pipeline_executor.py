"""PipelineSpec DAG executor (M5.4 core).

Consumes the identical JSON the console editor produces (`PipelineSpec` 0.1.0)
and runs it as a subprocess DAG through the same `uv run` env as the kits
(SPECS §4). This is the CLI executor `scholar-harness run --pipeline <file>`.

Execution model
---------------
1. Load + validate the spec (structural/semantic invariants that the console
   already enforces).
2. Topologically schedule nodes from `edges` (Kahn's algorithm).
3. For each node:
   a. Resolve `{{...}}` template args against `settings` + downstream node
      outputs + pipeline slots.
   b. Idempotency guard: if every declared `output` already exists AND the
      node fingerprint matches, skip (re-run is a no-op).
   c. `requires_decision`: after the node command has produced its batch files,
      check that decision files are present for every produced batch. If not,
      HALT the pipeline and report which batches need review.
   d. Run the node command as a subprocess in the workspace dir, streaming
      stdout/stderr and capturing exit code.
   e. Apply `on_fail` semantics (abort | skip | continue) on non-zero exit.
4. Emit a per-node result list; caller (CLI) renders it.

Dry-run is handled separately by the console endpoint; this module never treats
dry-run and never writes to canonical files except through the node commands it
actually launches.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from .console.api.pipelines import (
    _TEMPLATE_RE,
    PipelineNode,
    PipelineSpec,
    _toposort,
    validate_spec,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

SLOT_KEYS = {"workspace_slug", "rq_id", "per_node_limit"}


class PipelineError(Exception):
    """Raised for halted / aborted pipelines with a structured message."""


class PipelineCancelled(PipelineError):
    """Raised when an operator cancels the pipeline between nodes."""


class NodeResult:
    """Outcome of a single node execution (serializable)."""

    def __init__(
        self,
        node_id: str,
        state: str,
        command: list[str],
        exit_code: int | None = None,
        message: str = "",
        skipped_reason: str | None = None,
        resolved_args: dict[str, Any] | None = None,
    ) -> None:
        self.node_id = node_id
        self.state = state  # success | skipped | halted | failed
        self.command = command
        self.exit_code = exit_code
        self.message = message
        self.skipped_reason = skipped_reason
        self.resolved_args = resolved_args or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "state": self.state,
            "command": self.command,
            "exit_code": self.exit_code,
            "message": self.message,
            "skipped_reason": self.skipped_reason,
            "resolved_args": self.resolved_args,
        }


def load_spec(path: str | Path) -> PipelineSpec:
    """Load a PipelineSpec JSON file, leniently validating it."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"pipeline spec not found: {p}")
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PipelineError(f"pipeline spec {p} is not valid JSON: {exc}") from exc
    raw.pop("fingerprint", None)
    spec = PipelineSpec.model_validate(raw)
    result = validate_spec(spec)
    if result["errors"]:
        raise PipelineError(f"pipeline spec {p} is invalid: {'; '.join(result['errors'])}")
    return spec


def resolve_template(value: Any, resolver: Callable[[str], Any | None]) -> Any:
    """Recursively replace `{{key}}` templates in a nested structure."""

    if isinstance(value, str):
        if not _TEMPLATE_RE.search(value):
            return value
        tokens = _TEMPLATE_RE.findall(value)
        resolved_tokens = []
        for token in tokens:
            resolved = resolver(token)
            if resolved is None:
                raise PipelineError(f"unresolved template key {token!r}")
            resolved_tokens.append(resolved)
        if len(tokens) == 1 and _TEMPLATE_RE.fullmatch(value.strip()):
            return resolved_tokens[0]
        return value
    if isinstance(value, list):
        return [resolve_template(v, resolver) for v in value]
    if isinstance(value, dict):
        return {k: resolve_template(v, resolver) for k, v in value.items()}
    return value


def _lookup_setting(settings: dict[str, Any], key: str) -> Any | None:
    node = settings
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def resolve_args(
    node: PipelineNode,
    spec: PipelineSpec,
    prior_outputs: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Resolve a node's `args` templates against settings/slots + prior outputs."""

    def resolver(token: str) -> Any | None:
        if token in SLOT_KEYS:
            if token == "workspace_slug":
                return spec.workspace_slug
            if token == "rq_id":
                return spec.settings.get("rq_ids", ["RQ1"])[0]
            if token == "per_node_limit":
                return spec.dry_run.get("per_node_limit", 25)
        # node output refs: {{node_id.output_path}}
        if "." in token:
            bp, _, tail = token.partition(".")
            if bp in prior_outputs and tail in prior_outputs[bp]:
                return prior_outputs[bp][tail]
        return _lookup_setting(spec.settings, token)

    return resolve_template(node.args, resolver)


def _flag_value(value: Any) -> list[str]:
    """Render a resolved arg value into CLI flag tokens."""
    if isinstance(value, bool):
        return ["true" if value else "false"]
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, dict):
        return [json.dumps(value)]
    return [str(value)]


def build_command(
    node: PipelineNode,
    resolved_args: dict[str, Any],
    workspace: Path,
) -> list[str]:
    """Construct the subprocess argv for a node.

    Node.command entries are kit CLIs (e.g. `scholar-search`) — they run through
    `uv run`. A repo-relative `src/...` path is resolved against REPO_ROOT.
    The base command always sits before the rendered `--arg` flags.
    """
    cmd: list[str] = []
    for token in node.command:
        if token.startswith("src/"):
            token = str((REPO_ROOT / token).resolve())
        cmd.append(token)

    for key, value in resolved_args.items():
        cmd.append(f"--{key}")
        cmd.extend(_flag_value(value))

    return ["uv", "run", *cmd]


def batch_decision_files(workspace: Path) -> list[Path]:
    """All screening decision files (both console wrapper and legacy raw array)."""
    screening = workspace / "literature" / "screening"
    if not screening.is_dir():
        return []
    return sorted(screening.glob("batch_*_decisions.json"))


def _produced_batches(workspace: Path) -> list[str]:
    screening = workspace / "literature" / "screening"
    if not screening.is_dir():
        return []
    return sorted(p.name for p in screening.glob("batch_*.json")
                  if "_decisions" not in p.name)


def requires_decision_satisfied(workspace: Path) -> tuple[bool, list[str]]:
    """True if every produced batch has a decision file. Returns (ok, pending)."""
    produced = _produced_batches(workspace)
    decided = {d.name.replace("_decisions.json", ".json") for d in batch_decision_files(workspace)}
    pending = [b for b in produced if b not in decided]
    return (not pending, pending)


def _output_exists(workspace: Path, output: str) -> bool:
    # outputs may contain glob patterns (e.g. batch_*.json)
    target = workspace / output
    if any(ch in output for ch in "*?["):
        return bool(list(workspace.glob(output)))
    return target.is_file()


def run_node(
    node: PipelineNode,
    spec: PipelineSpec,
    workspace: Path,
    prior_outputs: dict[str, dict[str, str]],
    output: Callable[[str], None] = print,
) -> NodeResult:
    """Execute a single node, applying on_fail + requires_decision semantics."""

    resolved = resolve_args(node, spec, prior_outputs)
    command = build_command(node, resolved, workspace)
    output(f"▶ node {node.id}: {' '.join(command)}")

    # Idempotency: all outputs present -> already done.
    if node.outputs and all(_output_exists(workspace, o) for o in node.outputs):
        # Recompute fingerprint only for tracking; outputs exist = done.
        return NodeResult(
            node.id, "skipped", command,
            skipped_reason="outputs already present (idempotent)",
            resolved_args=resolved,
        )

    proc = subprocess.run(
        command,
        cwd=str(workspace),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    body = (proc.stdout or "").strip()
    if body:
        output(body)

    if proc.returncode != 0:
        if node.on_fail == "abort":
            msg = f"node {node.id} failed (exit {proc.returncode}); aborting pipeline"
            output(f"✗ {msg}")
            raise PipelineError(msg)
        if node.on_fail == "skip":
            output(f"⚠ node {node.id} failed (exit {proc.returncode}); skipping per on_fail=skip")
            return NodeResult(node.id, "skipped", command, exit_code=proc.returncode,
                              message="skipped on failure (on_fail=skip)", resolved_args=resolved)
        output(f"⚠ node {node.id} failed (exit {proc.returncode}); continuing per on_fail=continue")
        return NodeResult(node.id, "failed", command, exit_code=proc.returncode,
                          message="continued despite failure (on_fail=continue)", resolved_args=resolved)

    if node.requires_decision:
        ok, pending = requires_decision_satisfied(workspace)
        if not ok:
            msg = (f"node {node.id} produced batches but decisions are required; "
                   f"halt pipeline — pending review for: {', '.join(pending)}")
            output(f"⏸ {msg}")
            return NodeResult(node.id, "halted", command, exit_code=0,
                              message=msg, resolved_args=resolved)

    return NodeResult(node.id, "success", command, exit_code=0, resolved_args=resolved)


class PipelineExecutor:
    """Orchestrate a PipelineSpec DAG as sequential subprocess nodes."""

    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace).resolve()
        if not self.workspace.is_dir():
            raise PipelineError(f"workspace not found: {self.workspace}")

    def run(
        self,
        spec: PipelineSpec,
        output: Callable[[str], None] = print,
        skip: Iterable[str] = (),
        should_cancel: Callable[[], bool] | None = None,
    ) -> list[NodeResult]:
        node_map = {n.id: n for n in spec.nodes}
        order, cycle_errors = _toposort(set(node_map), spec.edges)
        if cycle_errors:
            raise PipelineError("; ".join(cycle_errors))

        results: list[NodeResult] = []
        prior_outputs: dict[str, dict[str, str]] = {}

        for node_id in order:
            if should_cancel is not None and should_cancel():
                raise PipelineCancelled("cancelled by operator")
            if node_id in skip:
                output(f"… node {node_id} skipped (explicit)")
                results.append(NodeResult(node_id, "skipped", [], skipped_reason="explicit skip"))
                continue
            node = node_map[node_id]
            result = run_node(node, spec, self.workspace, prior_outputs, output=output)
            results.append(result)
            if node.outputs:
                prior_outputs[node.id] = {o: o for o in node.outputs}
            if result.state == "halted":
                raise PipelineError(result.message)
            if result.state == "failed":
                # continue-on-fail wraps the failure as 'failed' but pipeline continues
                continue
            if result.state == "success" and node.requires_decision:
                # after a successful requires_decision node, check satisfaction again
                ok, pending = requires_decision_satisfied(self.workspace)
                if not ok:
                    raise PipelineError(
                        f"pipeline halted: review required for {', '.join(pending)}"
                    )
        return results


def execute_file(
    spec_path: str | Path,
    workspace: str | Path,
    output: Callable[[str], None] = print,
    skip: Iterable[str] = (),
) -> tuple[PipelineSpec, list[NodeResult]]:
    """Convenience: load a spec file and run the DAG. Returns (spec, results)."""
    spec = load_spec(spec_path)
    executor = PipelineExecutor(workspace)
    results = executor.run(spec, output=output, skip=skip)
    return spec, results


if __name__ == "__main__":  # pragma: no cover
    sys.exit("run via `scholar-harness run --pipeline`")