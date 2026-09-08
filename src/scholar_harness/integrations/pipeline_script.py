"""Render a PipelineSpec into a standalone, equivalently-executing bash script.

M5.4 shell-script export (PLAN §4 deliverable 4): from the same `PipelineSpec`
the console editor produces, render a `#!/usr/bin/env bash` script that
materializes every node command (args resolved), schedules in topological
order, and reproduces the executor's runtime semantics:

  - idempotency guard (skip a node whose declared outputs already exist),
  - `on_fail` abort | skip | continue on non-zero exit,
  - `requires_decision` halt when produced screening batches lack decisions.

Executing the script produces the same workspace artifacts in the same order
as `uv run scholar-harness run --pipeline <spec>` (test proves parity).

Resolution follows `pipeline_executor.build_command`/`resolve_args` exactly:
`src/...` command tokens are materialized as absolute repo paths, template args
are resolved against `settings` + upstream node outputs + slots, and `--key`
flags are rendered with the same value flattening (`_flag_value`).
"""

from __future__ import annotations

from pathlib import Path

from ..console.api.pipelines import PipelineSpec, _fingerprint
from ..pipeline_executor import _toposort, build_command, resolve_args

SHELL_MSG = "uv run scholar-harness run --pipeline"


def _shell_quote(token: str) -> str:
    return "'" + str(token).replace("'", "'\\''") + "'"


def _render_node_call(node_id: str, spec, workspace: Path, prior_outputs) -> str:
    """Render one `run_node <id> <on_fail> <requires_decision> <outputs...> <cmd...>` line."""
    node = next(n for n in spec.nodes if n.id == node_id)
    resolved = resolve_args(node, spec, prior_outputs)
    command = build_command(node, resolved, workspace)

    parts = ["run_node", _shell_quote(node.id), _shell_quote(node.on_fail),
             _shell_quote("true" if node.requires_decision else "false")]
    parts.extend(_shell_quote(out) for out in node.outputs)
    parts.extend(_shell_quote(tok) for tok in command)
    return " ".join(parts)


def render_pipeline_sh(spec: PipelineSpec, workspace: Path) -> str:
    """Render `spec` into an equivalently-executing bash script string."""
    ws = Path(workspace).resolve()
    # POSIX-normalized path so `cd` works on Windows git-bash and POSIX alike
    ws_posix = ws.as_posix()

    fingerprint = spec.fingerprint or _fingerprint(spec)
    order, cycle_errors = _toposort({n.id for n in spec.nodes}, spec.edges)
    if cycle_errors:
        raise ValueError("; ".join(cycle_errors))

    lines: list[str] = [
        "#!/usr/bin/env bash",
        "# ============================================================================",
        "# Nexus Scholar Harness · PipelineSpec shell export",
        f"#   id:          {spec.id}",
        f"#   name:        {spec.name or '—'}",
        f"#   archetype:   {spec.archetype}",
        f"#   fingerprint: {fingerprint}",
        f"#   workspace:   {ws_posix}",
        f"# Scheduled {len(order)} nodes in DAG order; executes equivalently to:",
        f"#   {SHELL_MSG} <spec.json> -w {ws_posix}",
        "# ============================================================================",
        "set -uo pipefail",
        "",
        'ws="${1:-}"',
        "if [ -z \"$ws\" ]; then",
        f"  ws={_shell_quote(ws_posix)}",
        "fi",
        'cd "$ws" || { echo "workspace not found: $ws" >&2; exit 1; }',
        "",
        "run_node () {",
        "  local id=\"$1\"; shift",
        '  local on_fail="$1"; shift',
        '  local requires_decision="$1"; shift',
        "  # outputs = leading tokens; command = tokens until end",
        "  local -a outputs=()",
        '  while [[ "$1" != "uv" ]]; do outputs+=("$1"); shift; done',
        '  echo "▶ node $id: $*"',
        "",
        "  # idempotency guard: all declared outputs present -> already done",
        '  if [ "${#outputs[@]}" -gt 0 ]; then',
        "    local missing=0 _o",
        '    for _o in "${outputs[@]}"; do',
        '      case "$_o" in',
        '        *[*?[]* ) compgen -G "$_o" >/dev/null || missing=1 ;;',
        '        * ) [ -e "$_o" ] || missing=1 ;;',
        "      esac",
        "    done",
        '    if [ "$missing" -eq 0 ]; then',
        '      echo "… node $id skipped (outputs already present, idempotent)"',
        "      return 0",
        "    fi",
        "  fi",
        "",
        '  "${@}"',
        "  local rc=$?",
        '  if [ "$rc" -ne 0 ]; then',
        '    if [[ "$on_fail" == "abort" ]]; then',
        '      echo "✗ node $id failed (exit $rc); aborting pipeline"',
        "      exit 1",
        '    elif [[ "$on_fail" == "skip" ]]; then',
        '      echo "⚠ node $id failed (exit $rc); skipping per on_fail=skip"',
        "      return 0",
        "    else",
        '      echo "⚠ node $id failed (exit $rc); continuing per on_fail=continue"',
        "      return 0",
        "    fi",
        "  fi",
        "",
        '  if [[ "$requires_decision" == "true" ]]; then',
        "    local -a pending=() _b",
        '    for _b in literature/screening/batch_*.json; do',
        '      [[ -e "$_b" ]] || continue',
        '      case "$_b" in *_decisions.json) continue ;; esac',
        '      [[ -e "${_b%.json}_decisions.json" ]] || pending+=("$_b")',
        "    done",
        '    if [ "${#pending[@]}" -gt 0 ]; then',
        '      echo "⏸ node $id produced batches but decisions are required; halt — pending: ${pending[*]}"',
        "      exit 1",
        "    fi",
        "  fi",
        "}",
        "",
    ]

    prior_outputs: dict[str, dict[str, str]] = {}
    for node_id in order:
        lines.append(_render_node_call(node_id, spec, ws, prior_outputs))
        node = next(n for n in spec.nodes if n.id == node_id)
        if node.outputs:
            prior_outputs[node.id] = {o: o for o in node.outputs}
        lines.append("")

    lines.extend([
        f"echo \"✓ PipelineSpec {spec.id} complete (bash export)\"",
        "exit 0",
    ])
    return "\n".join(lines) + "\n"