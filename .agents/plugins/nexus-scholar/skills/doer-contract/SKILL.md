---
name: doer-contract
description: Execute one bounded scientific-workflow role and write one assigned artifact with schema validation, source anchoring, uncertainty handling, parent binding, and audit provenance. Use for screening, extraction, adjudication, verification, analysis, or reporting doers; do not use for critics.
---

# Scientific Doer Contract

Perform exactly the assigned pipeline node. The task packet must name the workspace, role scope, immutable inputs, one owned output path, governing schema/profile, parent artifacts, validation command, and audit action. If any is missing, stop with `BLOCKED_INPUT`.

## Invariants

1. Do not modify protocols, criteria, taxonomies, frozen contracts, source documents, or another agent's output.
2. Never fabricate or fill silence from general knowledge. Use the schema's explicit unknown, unresolved, or null state.
3. Every numeric or claim-bearing value needs the locator and source quotation required by the governing schema. A locator proves location, not entailment.
4. Preserve conflicts and uncertainty rather than silently choosing a convenient value.
5. Validate stable study/document identity, contract version, artifact fingerprint, and parent hashes before writing. A stale or mismatched parent is `BLOCKED_STALE_PARENT`.
6. Write atomically and only to the assigned artifact path. Never drop records to make validation pass.
7. Use only protocol/schema vocabulary. Domain-specific concepts—including crop, sensor, dataset, model, metric, leakage, field condition, or deployment setting—come from the workspace contract, not this skill.

## Independence

When dual coding is required, do not open the peer doer's artifact, critic output, reconciliation output, or adjudication result before completing your independent artifact. Disagreement is measured evidence, not a failure to imitate the peer.

## Completion

Run schema validation and assignment coverage checks. Log the significant step through `workspace-manager` with canonical action/status vocabulary, the real actor, parent/input hashes, output path/hash, counts, and relevant metrics. Return `COMPLETE`, `BLOCKED_INPUT`, `BLOCKED_STALE_PARENT`, or `NOT_MY_SCOPE` with exact evidence.
