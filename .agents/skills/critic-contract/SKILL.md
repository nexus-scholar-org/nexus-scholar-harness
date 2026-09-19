---
name: critic-contract
description: Adversarially review one scientific-workflow artifact against its schema, immutable sources, parent lineage, and role scope. Use for screening, extraction, verification, analysis, or reporting critics; do not use for doers or remediation.
---

# Scientific Critic Contract

Review one assigned artifact without modifying it. The only permitted write is the task packet's critique artifact. Never repair the reviewed artifact, change the protocol, or perform the doer's role.

## Required review axes

1. Schema and vocabulary: required fields, types, enums, cardinality, and no unapproved fields.
2. Lineage: stable identities, contract version, artifact fingerprint, parent hashes, and source hashes resolve to the assigned inputs.
3. Anchoring: locators and quotations exist and support the encoded value; false anchoring is critical.
4. Consistency: decisions, values, totals, row identities, and state transitions do not contradict one another.
5. Uncertainty: silence, conflicts, and unresolved cases retain explicit uncertainty instead of becoming false negatives, zeros, or absences.
6. Scope and independence: the doer stayed within its artifact and did not consume prohibited peer outputs.

## Findings and gate

Every finding needs an ID, severity (`critical|major|minor`), category, precise locator, observed evidence, violated requirement, and actionable recommendation. `PASS` requires zero critical and zero major findings. Any major yields `FAIL`; any critical yields `FAIL_ESCALATE`.

Deterministic validation and criticism are separate gates. A deterministic pass never cancels a critic failure. Emit the critique using the assigned schema/path, then report `PASS`, `FAIL`, `FAIL_ESCALATE`, or `BLOCKED_INPUT`.
