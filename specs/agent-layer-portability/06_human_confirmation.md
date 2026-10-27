# 06 — Human confirmation (`HumanConfirmation@1`)

Normative for Phase C. Owner decisions settled 2026-10-26 (see `05` §8 items 3/5):

- **Signing party = the customer's named reviewer.** The export narrative is "confirmed by a person", not "confirmed by the service". Records carry the person's name, affiliation, and signing capacity (`lead_reviewer`).
- **The pilot corpus is labelled, not backfilled.** No retrospective `HumanConfirmation` is generated for prior agent-mutual work; the absence of a confirmation artifact is itself the honest state that the export gate reports.

## 1. The problem

Phase B makes agent work verifiable, but the question "who accepted this?" still has no artifact. `588 included` is unprovable: nothing binds the set of decisions to a named human who saw exactly those bytes. A rubber-stamped checkbox would be worse than nothing, so the schema prices honesty in: overrides must carry reasons, deferrals are first-class, and the export gate verifies the reviewer saw the bytes the workspace now ships.

## 2. `HumanConfirmation@1` — payload shape

```json
{
  "schema": "HumanConfirmation@1",
  "retrospective": false,
  "reviewer": {
    "name": "string (non-empty)",
    "affiliation": "string (non-empty)",
    "signing_capacity": "lead_reviewer"
  },
  "artifacts": [
    { "path": "workspace-relative", "sha256": "64 hex", "label": "descriptive" }
  ],
  "decisions": [
    {
      "study_id": "string",
      "verdict": "confirmed | changed | deferred",
      "amended": "optional — required when verdict=changed",
      "rationale": "optional — required when verdict=changed",
      "defer_reason": "optional — required when verdict=deferred"
    }
  ],
  "summary": { "considered": 0, "confirmed": 0, "changed": 0, "deferred": 0 },
  "provenance": { "tool": "confirm_screening.py", "created_at": "ISO8601" }
}
```

`screens` (what the human reviewed) and `amends` (what changed) carry **disjoint** data — a row may say "changed" or "deferred", never partially both, and `confirmed` rows carry no amendments. Counts: `considered == len(decisions)` and `confirmed + changed + deferred == considered`. Study ids are unique. `provenance.created_at` is timing metadata: it is excluded from any identity digest (reuse the Phase B convention).

## 3. Binding (what "Saw it" means)

1. `artifacts` must cover **every** decision artifact present in `literature/screening/` at sign time: `batch_NNN_decisions.json`, plus `batch_NNN_decisions_screener2.json` in dual-screen mode, plus `_adjudication_resolved_group_*.json` when adjudicated. A signing run that detects uncovered artifacts refuses `BLOCKED_INPUT` naming the missing paths — the reviewer does not partially bless a set.
2. Each `sha256` is over the file bytes as the reviewer saw them (streamed, not via a cached registry entry).
3. **Verification of the binding is the export-side duty:** at validate-time and at export-time the current on-disk bytes must reproduce every recorded `sha256`. A mismatch is `PARENT_HASH_MISMATCH` (existing refusal code; a changed artifact after review is exactly a parent-hash mutation), never a warning, never a silent re-hash to the new bytes. This implements plan acceptance criterion 1 — a confirmation cannot silently bind to mutated bytes; the verify step refuses, and the remedy is a fresh confirmation against the new artifact.

## 4. Producer and consumers

- **Producer:** `scripts/confirm_screening.py <workspace>` — interactive or `--from-queue` (a simple JSON of intended rows), validates the schema locally, re-verifies every artifact hash *at write time*, then writes `literature/screening/HUMAN_CONFIRMATION.json` + an audit-journal event naming the reviewer. It never signs for someone: the reviewer identity is supplied explicitly, confirmed interactively, and recorded. Residual risk (accepted): the write lands *before* the journal append, so a journal failure after a successful write leaves a signed record with no audit event — surface this as a warning if the append fails, never silently re-sign.
- **Consumers:**
  - `scholar_harness.contracts.confirmation` — `validate(record, *, verify_artifacts=False)`, `verify_artifacts(record, root)`, following the module conventions of the envelope package (named refusals, no broad exceptions).
  - **Export gate (plan criterion 4):** an export claiming "confirmed" (the `--claim-confirmed` path of `scholar-harness export`) refuses a named refusal (frozen registry code `REFUSED_UNSUPPORTED`, detail starting "no human confirmation artifact") unless a valid `HUMAN_CONFIRMATION.json` exists whose every artifact hash verifies against the current tree *at export time*, and whose `retrospective` is `false`. Retrospective records may never satisfy the export gate (criterion 5) — they exist only for schema compatibility and are labelled in any rendering. (The registry is frozen per §7; `REFUSED` is not a member — the export-gate-only refusal is realized with `REFUSED_UNSUPPORTED`.)
  - The envelope wraps confirmation exactly like any other payload; closure guarantees apply.

## 5. Honesty pricing (anti-rubber-stamping)

- `changed: true` rows require a `rationale`; the validator refuses otherwise (criterion 3, from `05`).
- `deferred` rows are visible in the summary and any export rendering; a deferral is a decision, not an omission.
- No tooling rewards 100% confirmation rate: nothing in the schema, validator, or export gate treats `all confirmed` as preferable. High override rates are surfaced, not suppressed.
- An override (interactive or `--from-queue`) naming a `study_id` absent from the decision artifacts refuses `INVALID_OUTPUT` — silently dropping it would record that study as `confirmed` behind the reviewer's back.

## 6. Negative cases (all must be named rejections)

1. Confirmation referencing a stale artifact hash → `PARENT_HASH_MISMATCH`, with rejected.
2. `changed: true` with null/empty `rationale` → `INVALID_OUTPUT`.
3. Any `summary` count disagreeing with the rows → `INVALID_OUTPUT`.
4. Missing decision artifact coverage (e.g. a screener2 file exists, unsigned) → `BLOCKED_INPUT` naming the file.
5. `retrospective: true` record relied on at export → `REFUSED_UNSUPPORTED`.
6. Duplicate `study_id` → `INVALID_OUTPUT`.
7. Export claiming confirmed with no `HUMAN_CONFIRMATION.json` → `REFUSED_UNSUPPORTED` ("no human confirmation artifact").
8. Mutating a decision file after export → next export gate run verifies against the current bytes and refuses `PARENT_HASH_MISMATCH`.
9. `--claim-confirmed` without the `HUMAN_CONFIRMATION.json` artifact → `REFUSED_UNSUPPORTED`; with a retrospective record → `REFUSED_UNSUPPORTED`; with mutated decision bytes → `PARENT_HASH_MISMATCH`. The gate never silently re-hashes or re-validates after mutation.

## 7. Non-goals

- No cryptographic signing infrastructure (names + hashes, not PGP); the artifact hash chain is the trust primitive.
- No backfill tooling for existing corpora — the pilot stays labelled agent-mutual.
- No changes to `ScreeningDecisions@1`, envelope contract, or refusal registry enum.
