# Specifications

Formal specifications that the code and the frozen Contract v1 baseline still
cite. Kept because removing them would leave code comments, agent prompts or
baseline-locked documents pointing at nothing; several describe intent that
the [assessment](../docs/assessment/README.md) found not yet met.

| Series | Status |
| :-- | :-- |
| [`deep-audit-remediation-2026-09-17/`](deep-audit-remediation-2026-09-17/README.md) | Contract v1 (`10_cross_kit_contracts.md`) and the WP roadmap (`12_execution_roadmap.md`) are **baseline-locked** and cited by the agent prompts; `01`–`09` are the per-package requirement specs. Kit specs predate the 2026-11-03 merge into one package. |
| [`agent-layer-portability/`](agent-layer-portability/README.md) | Role model, envelope and refusals, skills portability, capability adapters, human confirmation. Implemented in `scholar_harness.contracts`, `capabilities`, `skills_portability`. |
| [`exploratory-grounding-agent/`](exploratory-grounding-agent/) | Historical (complete). Kept: lifecycle (`03`), cache-key format (`04`), MCP integration (`09`), evaluation (`13`), agent loops (`14`), inception improvements (`16`) — all cited from `src/`. |
| [`inception-ecosystem/`](inception-ecosystem/README.md) | Skill boundaries, handoffs, skill tree and plugin bundle (`scripts/sync_skills_bundle.py`). |
| [`handoff/`](handoff/README.md) | Agent handoff state machine (`scholar_harness.handoff`). |
