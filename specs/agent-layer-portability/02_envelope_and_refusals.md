# 02 — Envelope and Refusals

Every role boundary returns the same shape. The envelope is **transport**, not science: it says what happened to a request, never what a paper means.

> **Disambiguation that matters:** a screening verdict of `EXCLUDE` is *payload*, not a refusal. `PENDING` is payload too. Envelope `status` describes whether the role did its job, not what the role concluded. Conflating the two is how "no result" silently becomes "excluded."

---

## 1. Scope and relationship to Contract v1

This envelope wraps existing scientific artifacts. It does **not** redefine them.

| Layer | Example | Frozen by |
|---|---|---|
| Domain payload | `ScreeningDecisions@1`, `ExtractionRecord@1`, `ScreeningCritique@1` | `docs/architecture/contract_v1_baseline.md` |
| Transport | `Envelope@1` | this spec |

An envelope may carry a `ScreeningDecisions@1` payload. It may never add fields to it, reinterpret a `PENDING`, or downgrade a `PARTIAL` coverage claim. If a payload needs a new field, that is a Contract v1 decision with regenerated schemas and golden fixtures — not an envelope change.

## 2. Schema

```json
{
  "envelope": 1,
  "envelope_id": "ENV-20261023T101500Z-4f2a91",
  "role": "screener",
  "role_version": "2.1.0",
  "task_id": "T-SC-014",
  "arm": "B",
  "created_at": "2026-10-23T10:15:00Z",
  "status": "OK",
  "retryable": false,
  "human_action_required": false,
  "refusal": null,
  "coverage": { "expected": 50, "produced": 50, "unit": "records" },
  "inputs": [
    { "schema": "ScreeningBatch@1", "path": "literature/screening/batch_0113.json",
      "sha256": "9ae1f97d...", "role_version": null }
  ],
  "parents": [
    { "artifact": "protocol.json", "sha256": "3b71c0aa..." },
    { "artifact": "SCREENING_CRITERIA.md", "sha256": "0c9d2e41..." }
  ],
  "output": { "schema": "ScreeningDecisions@1", "data": { "...": "..." } },
  "output_sha256": "77ab0f12...",
  "provenance": {
    "adapter": "opencode|in-process",
    "adapter_version": "1.4.0",
    "isolation": "redacted-input",
    "blinded_from": ["screener@A"],
    "duration_ms": 41230
  }
}
```

### Field rules

| Field | Rule |
|---|---|
| `envelope_id` | Deterministic over the immutable fields (§4). Never random. |
| `role`, `role_version` | Must match a `roles/<id>.json`. Unknown role ⇒ `INVALID_OUTPUT` at the consumer. |
| `arm` | `A`/`B`/`null`. Present whenever `isolation` is not `none`. |
| `status` | Closed enum (§3). No free strings. |
| `retryable` | Whether the same request could succeed later unchanged. Drives app behaviour. |
| `human_action_required` | Whether a person must intervene (missing input, adjudication needed, policy refusal). |
| `coverage` | Required whenever `status ∈ {OK, PARTIAL}`. `produced < expected` forces `PARTIAL`. |
| `refusal` | Required iff `status ∈ {BLOCKED_INPUT, BLOCKED_*, REFUSED}`; must be `null` otherwise. |
| `inputs[]`, `parents[]` | Each entry carries a content hash. Downstream verifies before consuming. |
| `output_sha256` | Hash of the payload only. Two runs producing identical payloads agree here even if they differ in timing. |
| `provenance` | Filled by the adapter, not the role. A role cannot claim it was blinded. |

## 3. Status algebra

| Status | Output present? | Meaning | Required companions |
|---|---|---|---|
| `OK` | yes | Complete and schema-valid | `coverage.produced == expected` |
| `PARTIAL` | yes | Valid but incomplete | `coverage` with `produced < expected`, plus `refusal.codes[]` |
| `BLOCKED_INPUT` | **no** | A required input is absent or unreadable | `refusal.code`, `refusal.detail`, `refusal.missing[]` |
| `BLOCKED_AMBIGUOUS_TASK` | no | Instructions insufficient to proceed safely | `refusal.detail` naming the ambiguity |
| `BLOCKED_CANONICAL_REPO` | no | External repo/sync obligation cannot be met | `refusal.detail` naming the repo and evidence |
| `BLOCKED_BASELINE_DRIFT` | no | Frozen baseline failed `--check` | `refusal.detail` with the failing command |
| `REFUSED` | no | Policy refusal, including declared-unsupported (`E1`/`E2`/`E3`) | `refusal.code` from registry |
| `INVALID_OUTPUT` | yes | Payload produced but failed validation | `refusal.detail` with validator findings; payload retained for forensics |
| `GATE_FAILED` | n/a | A harness gate (test/review) rejected the change | `refusal.detail` + gate evidence |

### Invariants

```
OK            ⇒ output ≠ null ∧ validates ∧ coverage.produced == coverage.expected
PARTIAL       ⇒ output ≠ null ∧ validates ∧ coverage.produced < coverage.expected
BLOCKED_*     ⇒ output == null ∧ refusal ≠ null ∧ human_action_required == true
REFUSED       ⇒ output == null ∧ refusal.code ∈ registry
INVALID_OUTPUT⇒ output ≠ null ∧ validation_findings non-empty
```

A `BLOCKED_INPUT` that ships a partial payload is a defect: it invites downstream use of data the role did not stand behind. The validator rejects it.

## 4. Hashing and identity

Two hashes, two purposes:

| Hash | Covers | Used for |
|---|---|---|
| `output_sha256` | Canonical JSON of `output.data` only | Downstream parent binding |
| `envelope_id` | `role`, `role_version`, `task_id`, `arm`, `status`, `inputs[*].sha256`, `parents[*].sha256`, `output_sha256` | Reproducibility and dedup of runs |

Rules:

- Canonical serialisation follows `scholar_harness.contracts.canonical`: sorted keys, no insignificant whitespace, UTF-8, no `NaN`/`Infinity`, explicit `null`.
- `created_at`, `duration_ms`, and `provenance.adapter*` are **excluded** from both hashes. Timing must never change identity.
- A content-addressed artifact that is re-run with identical inputs and identical output yields the same `envelope_id`. Two different `envelope_id`s with identical `output_sha256` mean the inputs differed — a fact worth surfacing.

## 5. Parent binding

Every consumer verifies before use:

1. `parents[*].sha256` matches the file on disk.
2. `inputs[*].sha256` matches what the producer recorded.
3. If `isolation != none`, `provenance.blinded_from` is consistent with the role's declaration.

A mismatch is not a warning. It is `INVALID_OUTPUT` with `refusal.code = PARENT_HASH_MISMATCH` and the change is rejected. Silent re-binding is how a corrected protocol gets charted against an uncorrected screening run.

## 6. Refusal registry

Closed set. Adding a code requires editing this list and the role that may emit it, in the same change.

### Global

| Code | Emitted by | Meaning |
|---|---|---|
| `BLOCKED_INPUT` | any | Required artifact missing/unreadable |
| `BLOCKED_AMBIGUOUS_TASK` | coder, orchestrator | Task under-specified |
| `BLOCKED_CANONICAL_REPO` | coder, orchestrator | Toolkit sync obligation unmet |
| `BLOCKED_BASELINE_DRIFT` | coder, orchestrator, reviewer | Frozen baseline check failed |
| `REFUSED_UNSUPPORTED` | any | Declared-unsupported operation (`E1`/`E2`/`E3`) |
| `INVALID_OUTPUT` | any | Schema or invariant violation |
| `PARENT_HASH_MISMATCH` | any consumer | Lineage broken |
| `SCOPE_VIOLATION` | any | Attempted read/write outside `read_glob`/`write_glob` |

### Screening

| Code | Meaning |
|---|---|
| `CRITERIA_HASH_MISMATCH` | `criteria_sha256` ≠ protocol fingerprint |
| `BATCH_INCOMPLETE` | Decision coverage < 100% |
| `IDENTITY_AMBIGUOUS` | Record identity unresolvable (title collision, DOI conflict) |
| `BATCH_ID_MISMATCH` | `batch_id` disagrees between batch and decisions |

### Extraction

| Code | Meaning |
|---|---|
| `SOURCE_MISSING` | Required source text absent |
| `LOCATOR_UNRESOLVED` | Locator does not resolve in the source |
| `QUOTE_NOT_IN_SOURCE` | Quotation fails verbatim check |
| `ABSENCE_UNCLASSIFIED` | A required field is absent without an absence state |

### Review / test

| Code | Meaning |
|---|---|
| `VERDICT_CHANGES_REQUESTED` | Reviewer requests repairs (payload, not a refusal) |
| `REQUIREMENT_UNTRACEABLE` | Diff contradicts or omits a governing requirement |
| `TEST_GATE_FAILED` | Declared gate command failed |

## 7. Worked examples

### 7.1 `BLOCKED_INPUT` — a real case from this repository

`screening` was requested for a workspace whose `literature/included.json` did not exist.

```json
{
  "envelope": 1,
  "role": "screener",
  "role_version": "2.1.0",
  "task_id": "OA-COUNT-01",
  "status": "BLOCKED_INPUT",
  "retryable": true,
  "human_action_required": true,
  "refusal": {
    "code": "BLOCKED_INPUT",
    "detail": "workspaces/uav-crop-weed-v03/literature/included.json absent; literature/, pdfs/, extracted/ are empty",
    "missing": ["literature/included.json"]
  },
  "coverage": null,
  "inputs": [],
  "parents": [],
  "output": null,
  "output_sha256": null
}
```

Note what the envelope buys: a consumer can render "3 reasons this row is missing" without parsing a stack trace, and the missing set is machine-readable.

### 7.2 `REFUSED` — declared-unsupported

```json
{
  "status": "REFUSED",
  "retryable": false,
  "human_action_required": true,
  "refusal": {
    "code": "REFUSED_UNSUPPORTED",
    "detail": "E2: PDF acquisition for records without DOI or arXiv id is not supported by scholar-pdf-kit",
    "unsupported": "E2",
    "alternatives": ["supply the PDF manually", "exclude with logged reason"]
  }
}
```

### 7.3 `OK`

Requires `coverage.produced == coverage.expected`, a schema-valid payload, and matching `output_sha256`.

## 8. Validation

```
uv run python -m scholar_harness.contracts.envelope validate <path>
uv run python -m scholar_harness.contracts.envelope diff <a> <b>
```

Validation order: schema → invariants (§3) → hashes (§4) → parent binding (§5) → role existence and version compatibility.

### Negative test matrix

| Case | Expected |
|---|---|
| `status: OK` with `output: null` | reject |
| `status: BLOCKED_INPUT` with a payload | reject |
| `status: OK` with `coverage.produced < expected` | reject; must be `PARTIAL` |
| `status: PARTIAL` without `coverage` | reject |
| `refusal` present with `status: OK` | reject |
| Free-string status (`status: "failed"`) | reject |
| `envelope_id` recomputed differs | reject (tamper) |
| `parents[0].sha256` stale vs disk | `PARENT_HASH_MISMATCH` |
| Role id not in `roles/` | reject |
| `provenance.blinded_from` claims a role the declaration forbids | reject |

## 9. Why not reuse the existing artifact schemas as envelopes

Because they answer a different question. `ScreeningDecisions@1` says *what was decided*. The envelope says *whether the deciding role could do its job, on which inputs, under which isolation, and with what coverage*. Merging them would mean a schema change every time transport policy changes — and policy changes far more often than science.

Keeping them separate is also what allows the same payload to be produced by a human, an agent, or an import path, with the envelope recording which.
