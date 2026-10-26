# Decision record — Phase B envelope (2026-10-26)

Task packet: `packet_t_alp_b_envelope.md`. Governing spec:
`specs/agent-layer-portability/02_envelope_and_refusals.md` (including the
2026-10-26 `PROVIDER_TRANSIENT` amendment).

These are the judgement calls a later reviewer cannot reconstruct from code.

## D1 — the envelope module is a *package*, not a flat module

`scripts/generate_contract_baseline.py` locks `src/scholar_harness/contracts/*.py`
and `…/schemas/v1/*.json` with a **non-recursive** glob. A flat
`contracts/envelope.py` or a schema at `schemas/v1/envelope.schema.json` would
enter the frozen WP-00 lock set and fail `--check` — which the packet forbids
both touching and violating (criterion 6). The transport layer is therefore:

- `src/scholar_harness/contracts/envelope/` (package: `model.py`, `registry.py`,
  `api.py`, `schema.py`, `cli.py`) — same import surface,
  `scholar_harness.contracts.envelope`;
- `src/scholar_harness/contracts/schemas/envelope/envelope.schema.json` —
  outside the `schemas/v1/` frozen glob, generated from the pydantic model and
  pinned byte-identical by a test.

No lock file is touched; `generate_contract_baseline.py --check` stays green.

## D2 — PARTIAL counts as a refusal-bearing status

`02` §2 says refusal "must be null otherwise" (other than the refusal-required
statuses), but §3 requires PARTIAL to carry `refusal.codes[]` naming the gap.
Resolved in favour of §3 (the more specific rule): PARTIAL carries the refusal;
OK is the only refusal-free status. The final §8-matrix check ("refusal present
with a non-refusal status") uses this widened set. An `OK` carrying a refusal
still names itself: "refusal must be null for OK".

## D3 — `envelope_id` shape deviates cosmetically from the §2 example

The §2 example id is `ENV-20261023T101500Z-4f2a91`, embedding a timestamp. A
timestamp prefix would make `created_at` affect identity, contradicting
criterion 3 and the §4 rule "timing must never change identity". The rendered
id is `ENV-<16 hex>` — deterministic over the accordion of §4 fields, computed
with `scholar_harness.contracts.canonical.canonical_json_bytes` (no second
canonicaliser).

## D4 — `verify_parents` hashes parent files by raw content bytes

`output_sha256` is canonical-JSON-of-payload per §4, but parent entries name
arbitrary artifacts (`protocol.json`, `SCREENING_CRITERIA.md`). "Matches the
file on disk" therefore means **raw file bytes** for `parents[*]`/`inputs[*]`
disk verification. A missing file is `BLOCKED_INPUT` (no artifact is missing a
hash — it is missing entirely); a present file with a different hash is
`PARENT_HASH_MISMATCH`. Both raise; neither is a warning.

## D5 — payload strictness: outer object strict, nested forward-compatible

Contract v1 data models are `extra="allow"` by design (unknown minor-version
fields flow), so the payload's *own* schema cannot reject an undefined field;
02 §8 still requires the envelope not to rescue it. Compromise (documented in
code and tests): for payloads whose `schema` maps to a Contract v1 data model
(`ScreeningDecisions@1`, `ScreeningBatch@1`, `CorpusSnapshot@1`,
`DocumentManifest@1`, `ClaimsLedger@1`), the top-level payload object is
checked strictly against the schema's declared fields; nested objects keep the
frozen forward-compat policy. Unknown payload `schema` names travel opaquely
and unvalidated — the envelope never invents a validation the payload does not
carry, and never blocks a payload type it does not know (that is also why
`BLOCKED_INPUT` with payload is a status-level rejection, not a schema call).

## D6 — `GATE_FAILED` decision (spec silence)

§3 lists no invariant for `GATE_FAILED`; §2's field-rule misses it in the
"refusal required" enumeration while §3 requires "refusal.detail + gate
evidence". Decision: `GATE_FAILED` requires a refusal and ships no payload —
mirroring the blocked-family semantics without inventing a
`human_action_required` requirement the invariant list never states.

## D7 — `VERDICT_CHANGES_REQUESTED` is not a refusal

Screening it into the enum would make "reviewer wants changes" machine-legible
as a transport failure; the reviewer packet/format treats it as payload. It is
excluded from `RefusalCode`, appears in `docs/architecture/refusals.md` as an
annotated payload row (criterion 7 needs every code in the generated docs), and
the validator rejects any envelope claiming it as a refusal code.

## D8 — role-layer compatibility rules (currently un-spec'd)

`01` §"Semver in the envelope" gives roles semver and reproducibility but no
compatibility predicate. Enforced (all naming themselves as `INVALID_OUTPUT`):

1. `role` must exist in `roles/<id>.json`;
2. `role_version`'s **major** must equal the record's (minor/patch drift is
   compatible; majors are distinguishable runs);
3. each claimed refusal code is registry-listed, belongs to the role per the
   §6 "Emitted by" roles (or the any-role set, incl. adapter-emitted
   `PROVIDER_TRANSIENT`), and is consistent with the record's own codes;
4. `arm` is required when `isolation != "none"` per §2;
5. `blinded_from` entries (`role@arm` or `role`) are accepted only when the
   role declaration grants them or when they name the same role's *other*
   arm (§2's own `screener@A` example on a screener record whose declaration
   is otherwise empty).

Roles with no declared `blinded_from` still accept peer-arm entries — that is
§2's illustrative semantics; anything else is rejected.

## D9 — transient / retry identity

Tests prove a retried attempt (different `created_at`, `duration_ms`,
`adapter`, `adapter_version`) recomputes to the same `envelope_id`, and that
every immutable field or hash change produces a different id. Runtime wiring is
Phase E's; only the library and CLI exist here.

## D10 — CLI diff exit code

`diff` exits 0 with a JSON report whether or not the envelopes differ
(report semantics); every *violation* (bad load/validation/role check) exits 1
with a JSON refusal on stderr.

## D11 — role records are the schema-name authority (repair T-ALP-B)

**Finding (independent tester, adversarial pass).** `validate` ran payload
validation only when `output.schema` matched one of the five
`PAYLOAD_MODELS` names; any near-miss — `ScreeningDecisions@2`,
`ScreeningDecisions`, `ScreeningDecisions2@1`, `screeningdecisions@1` —
silently bypassed all payload validation. A one-character typo in a field the
consumer relies on was a fail-open route to acceptance.

**Fix.** Role records (`roles/<id>.json`, Phase A artifacts, read-only)
declare both directions: `outputs[].schema` and `inputs[].schema`. The
role-compatibility step (spec §8 step 5) now enforces, each as a named
`INVALID_OUTPUT` refusal quoting both the claimed and the declared names:

1. `output.schema` must be declared by the record (or the record declares no
   output schemas — see residual below);
2. every `inputs[*].schema` must be declared by the record;
3. a *declared but unregistered* output schema (declared by the record, absent
   from `PAYLOAD_MODELS`) is refused: an envelope whose payload nobody in the
   harness can validate must not pass silently.

**Placement.** The check sits in step 5 of the §8 order (schema → invariants →
hashes → parents → role compatibility), with the other role-record
cross-checks; §8's order is unchanged. Payload-schema validation for a
registered name stays where it was (invariant step, §3's "output validates").

**Residual, stated honestly.** A *registered* name is still the only route to
payload validation, and that is contractual: the envelope cannot validate a
payload for a schema it has no model for — inventing one would reimplement
Contract v1 outside the frozen registry. The operator-facing consequence is
that a role must declare a registered schema for anything riding an envelope.
Also, when `validate` is called with `roles_dir=None` (library consumers that
skip role cross-checks, e.g. `diff`), no role record exists to check against,
so an unregistered name still travels opaquely there; the CLI always supplies
`--roles-dir` or auto-discovers it, so the shipped command surface checks.
Records that declare neither `outputs` nor `inputs` (no shipped record today —
all eleven declare both) keep the opaquely-travelling behaviour; the code
comments say so rather than guessing.

## D11a — CLI fail-loud on undiscoverable roles (reviewer F1, cycle 2)

The `roles_dir=None` contract of `validate()` above stays: library consumers
may skip role cross-checks deliberately. The CLI however never silently
degenerates into that contract — when neither `--roles-dir` nor CWD discovery
yields a `roles/` directory, `python -m …envelope validate` refuses with a
`BLOCKED_INPUT` refusal on stderr naming `--roles-dir` (exit 1). A role-record
cross-check that would be skipped is never an acceptance.
