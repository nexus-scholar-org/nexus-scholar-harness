# AG-04: one screening worker with minimal researcher review on the protected publisher

**Status:** OPEN — implementation packet. **Lane:** RELEASE (changes the supported scientific/publication interaction).
**Supported deployment:** Windows MIC protected publisher (AG-03A proven); POSIX unproven.
**Parent:** [AG architecture decision](agent_controls_decision.md); builds on AG-03A (`binding.py`, `isolation.py`), AG-03B (`lifecycle.py`), AG-03C (`generations.py` + gated collect + currentness consumers).
**Interface choice:** CLI (`agent_screen.py` extension). No UI build, no second interface.

## 1. Objective

One usable, operator-attended screening workflow on the proven publisher:

> prepare a bound batch → one worker produces recommendations → the researcher
> reviews them → overrides create a preserved superseding revision → the
> authorized operator approves the exact reviewed content → the protected
> publisher collects it → downstream consumers recognize the current generation.

Connect the existing AG-02/03 controls into a small usable interaction. This is
NOT a new authority system, NOT a broad application, and NOT autonomous
scientific decision-making.

## 2. Worker and backend

- **One worker, one backend:** a local deterministic CLI worker (`recommend`
  command). It reads the assigned immutable batch + verified source material and
  writes draft recommendation rows ONLY to `literature/screening/recommendations/`.
- The worker makes NO scientific judgments: each row preserves the study
  identifier, criterion references, source locators, and uncertainty, with the
  decision carried as explicitly unresolved/pending review. No model accuracy is
  claimed from workflow execution.
- The worker cannot write publisher state (approval, policy, registry, audit,
  final outputs) — enforced by record location (recommendations dir only) and
  testable under a Low-IL worker process reusing AG-03A isolation.
- Worker failure, unavailable backend (missing batch/material), and invalid
  recommendations produce explicit typed recoverable states with no publication.

## 3. Researcher review and operator approval

- `review` displays the exact immutable snapshot bytes used for parsing, hashing
  and approval: decision, supporting reasons, uncertainty, source/criterion
  references, parent hashes. Read-only; protocol/batch identity inspectable
  without burdening the main flow. Instructions and errors in researcher language.
- Researcher resolutions arrive as a reviewed file; `approve` diffs it against
  the snapshot: identical → approve as-is; different → superseding revision
  preserving the original (AG-03B `supersede`), requiring fresh approval bound
  to the new revision. Stale approval can never authorize a changed revision.
- `OperatorIdentity` comes ONLY from the publisher-owned operator context
  (`literature/screening/operator_context.json`, worker-unwritable). A typed
  name, reviewer string, or editable approval file is never trusted identity.
  On Windows, `approve` refuses when its own process token is Low integrity —
  the worker cannot invoke the operator action.
- MAYBE/CONFLICT stay unresolved until the researcher resolves them or defers
  publication (`defer --reason`; reason CANCELLED is an explicit cancellation).
  Missing approval is never a default approval.
- Collection uses the existing AG-03C gate and generation commit point;
  downstream currentness checks stay active. No bypass, no weaker shortcut: if
  the approval path cannot support the interaction securely, repair the bounded
  integration defect instead.

## 4. Scope and non-goals

Single-screener flow only. No POSIX expansion, toolkit changes, contract
weakening, multi-worker orchestration, autonomous exclusion, review dashboard,
extraction, synthesis, or held-out model evaluation. No AG-03 threat-model
repetition, no primitive reimplementation. Synthetic batches + disposable state
for implementation and tests. No UAV final outputs without valid accepted
parents, protocol readiness, and actual researcher approval (none claimed here).

## 5. Acceptance and validation

Demonstrate one complete supported Windows workflow (prepare → worker →
review → override-with-supersession → approve → publish → CURRENT downstream).
Focused tests: worker permissions/backend failure; invalid/incomplete
recommendations; unresolved decisions; override invalidating earlier approval;
display↔approval/publication tampering; cancel/defer; successful
current-generation publication. Reuse authority/generation/integrity tests; do
not duplicate every AG-03 negative. Targeted tests in-loop; final RELEASE gate
once; independent review + tester; gate commands from the F1 selector
(`select_test_gate.py --path … --stage …`).

## 6. Persistence

Record backend, interface, deployment, and residuals here on delivery. Update
the plan, README, and backlog to agree. Real-workspace mutation (none planned)
would require the workspace-manager audit logger; synthetic dirs are not
research events.
