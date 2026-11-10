# Specifications

Formal specifications that the code and the frozen Contract v1 baseline still
cite. Kept because removing them would leave code comments, agent prompts or
baseline-locked documents pointing at nothing; several describe intent that
the [assessment](../docs/assessment/README.md) found not yet met. Statuses
checked on 2026-11-10; the plan of record is
[`docs/roadmap/production-plan.md`](../docs/roadmap/production-plan.md).

| Series | Status |
| :-- | :-- |
| [`deep-audit-remediation-2026-09-17/`](deep-audit-remediation-2026-09-17/README.md) | Contract v1 (`10_cross_kit_contracts.md`) and the WP roadmap (`12_execution_roadmap.md`) are **baseline-locked** and cited by the agent prompts; their status lines are frozen with the baseline. `01`–`09` are the per-package requirement specs. Historical as a plan (2026-11-10): superseded by the production plan and the 2026-11-03 assessment; the PDF, RAG, graph and verify specs are parked, the bib spec governs no code (`scholar_bib` deleted in M5-slim). Kit specs predate the 2026-11-03 merge into one package. |
| [`agent-layer-portability/`](agent-layer-portability/README.md) | Delivered (Phases A–E merged, README §10). Role model, envelope and refusals, skills portability, capability adapters, human confirmation. Implemented in `scholar_harness.contracts`, `capabilities`, `skills_portability`. |
| [`exploratory-grounding-agent/`](exploratory-grounding-agent/) | Historical (complete). Kept: lifecycle (`03`), cache-key format (`04`), MCP integration (`09`), evaluation (`13`), agent loops (`14`), inception improvements (`16`) — all cited from `src/`. |
| [`inception-ecosystem/`](inception-ecosystem/README.md) | Live (checked 2026-11-10). Skill boundaries, handoffs, skill tree and plugin bundle (`scripts/sync_skills_bundle.py`). The browser inception flow (M4b) and recon over HTTP (M4c) sit beside these skills. |
| [`handoff/`](handoff/README.md) | Agent handoff state machine (`scholar_harness.handoff`). The code is present; the autonomous phase loop is not in the production plan (decision 2026-11-03) and the phases after screening are parked. |
