# Decision: agent-instruction reference repair (documentation-only)

**Date:** 2026-10-12 · **Status:** accepted · **Lane:** documentation-only

## Context

`tests/conformance/test_opencode_dev_agents.py` treats the OpenCode agent
definitions as contract-governed: `.opencode/agent/{coder,orchestrator}.md` are
listed in the frozen-contract baseline (`scripts/generate_contract_baseline.py`)
and their content drives how agents select and execute work.

Both files instructed agents to read two documents that **do not exist**:

| Referenced | Reality |
|---|---|
| `specs/deep-audit-remediation-2026-09-17/10_task_list.md` | There is no `10_task_list.md` in that directory. The file at `10` is `10_cross_kit_contracts.md` (the frozen cross-kit contract). |
| `specs/deep-audit-remediation-2026-09-17/12_remediation_roadmap.md` | The file is `12_execution_roadmap.md` (work packages WP-00…WP-14). |

Unlike a broken markdown link (which `test_agent_markdown_links_resolve` would
catch), these were **backticked code spans**, so no test failed. The defect was
practical: the orchestrator and coder were told to read files that cannot be
opened when selecting contract work.

## Decision

Repair the references to the real documents, **as a pure reference/ documentation
revision**:

- `10_task_list.md` → `10_cross_kit_contracts.md` (annotated "frozen cross-kit contract")
- `12_remediation_roadmap.md` → `12_execution_roadmap.md` (annotated "work packages and ordering")

The surrounding instruction (which files to read for contract work, and that the
frozen contract schemas + golden two-study chain are normative) is unchanged.

## Explicitly unchanged

This revision does **not** alter, and must not be read as altering:

- contract semantics, decision meanings, or the contract version;
- identifier rules (`workspace` / `study` / `document` / `chunk` identity);
- schemas or generated schema artifacts;
- golden fixtures;
- runtime behaviour of any component.

No file under `src/`, `tests/`, `tools/`, `packaging/`, or `workspaces/` changes
except the two agent definitions named above.

## Baseline handling (deliberate)

`.opencode/agent/{coder,orchestrator}.md` are inputs to the frozen-contract
baseline, so `docs/architecture/contract_v1_baseline.json` is **deliberately
regenerated** in this change after an explicit review of the exact intended
difference — the two files' recorded hashes, and nothing else.

The local working-copy edit to `.opencode/agent/reviewer.md` (a permission
change, uncommitted and intentionally kept by the operator) is **excluded**: the
regenerated baseline records the committed `reviewer.md` hash, so a clean
checkout remains baseline-clean.

## Verification

- `scripts/generate_contract_baseline.py --check` passes on the clean committed
  state (verified before and after the regeneration).
- Diffing the regenerated baseline against the previous one shows exactly two
  changed entries: `.opencode/agent/coder.md` and `.opencode/agent/orchestrator.md`.
- Schema, fixture, and pin `--check` generators remain green.
- `tests/conformance/test_opencode_dev_agents.py`, the contract-baseline
  conformance test, and the full suite pass on CI.
