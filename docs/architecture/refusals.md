# Refusal registry (generated)

<!-- GENERATED FILE — do not hand-edit; render via
     scholar_harness.contracts.envelope.registry.render_refusals_doc().
     Parity with the enum and the roles/ records is enforced by
     tests/conformance/test_envelope.py -->

Closed set of `Envelope@1` refusal codes (spec `02_envelope_and_refusals.md`
§6). Adding a code requires editing the spec, the enum, and the roles that
may emit it *in the same change*.

## Policy: transient provider failures

**The principle: provider failure is not empty success.** A rate limit, a
timeout, a dropped connection, or a context overflow means the role's
records are exactly as unresolved as before the call. Nothing is written,
nothing is counted, and no batch decision silently moves from `PENDING` to
`EXCLUDED`.

- Provider failure is `PROVIDER_TRANSIENT`, never `BLOCKED_INPUT` (no
  artifact is missing) and never `REFUSED` (nothing prohibited happened).
- **The role never retries.** Backoff policy, budget ceilings, and
  per-provider limits are adapter concerns. Retry exhaustion surfaces one
  final envelope whose refusal detail carries the attempt count.
- **Retries preserve identity.** `envelope_id` excludes timing, so the
  same request against the same inputs produces the same logical envelope
  whether it succeeded on the first attempt or the fourth.
- **Partially completed batches are `PARTIAL`, not `PROVIDER_TRANSIENT`;**
  the unfinished records keep their payload-neutral `PENDING` state.
- **Other codes are never auto-retried.** `BLOCKED_INPUT`, `REFUSED`,
  `SCOPE_VIOLATION`, and hash mismatches re-produce themselves.

## Global

| Code | Emitted by | Meaning |
|---|---|---|
| `BLOCKED_INPUT` | any | Required artifact missing/unreadable |
| `BLOCKED_AMBIGUOUS_TASK` | coder, orchestrator | Task under-specified |
| `BLOCKED_CANONICAL_REPO` | coder, orchestrator | Toolkit sync obligation unmet |
| `BLOCKED_BASELINE_DRIFT` | coder, orchestrator, reviewer | Frozen baseline check failed |
| `REFUSED_UNSUPPORTED` | any | Declared-unsupported operation (E1/E2/E3) |
| `PROVIDER_TRANSIENT` | adapter (any role) | Model/data provider unreachable, rate-limited, timed out, or context overflow. Retried by the adapter, never by the role; retry exhaustion surfaces to the human with the attempt count |
| `INVALID_OUTPUT` | any | Schema or invariant violation |
| `PARENT_HASH_MISMATCH` | any consumer | Lineage broken |
| `SCOPE_VIOLATION` | any | Attempted read/write outside read_glob/write_glob |

## Screening

| Code | Meaning |
|---|---|
| `CRITERIA_HASH_MISMATCH` | criteria_sha256 ≠ protocol fingerprint |
| `BATCH_INCOMPLETE` | Decision coverage < 100% |
| `IDENTITY_AMBIGUOUS` | Record identity unresolvable (title collision, DOI conflict) |
| `BATCH_ID_MISMATCH` | batch_id disagrees between batch and decisions |

## Extraction

| Code | Meaning |
|---|---|
| `SOURCE_MISSING` | Required source text absent |
| `LOCATOR_UNRESOLVED` | Locator does not resolve in the source |
| `QUOTE_NOT_IN_SOURCE` | Quotation fails verbatim check |
| `ABSENCE_UNCLASSIFIED` | A required field is absent without an absence state |

## Review / test

| Code | Meaning |
|---|---|
| `REQUIREMENT_UNTRACEABLE` | Diff contradicts or omits a governing requirement |
| `TEST_GATE_FAILED` | Declared gate command failed |

## Not a refusal — reviewed payload

The review table below is *payload*, not part of this refusal registry:

| Code | Meaning |
|---|---|
| `VERDICT_CHANGES_REQUESTED` | Reviewer requests repairs (payload, not a refusal) |

`VERDICT_CHANGES_REQUESTED` is deliberately absent from the
`RefusalCode` enum: a review verdict is data the consumer parses, not a
transport refusal. It may never appear in an `envelope.refusal.code`; the
validator rejects any attempt.

Registry revision: 19 codes.
