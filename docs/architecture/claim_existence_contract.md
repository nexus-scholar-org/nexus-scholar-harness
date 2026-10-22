# Claim-Existence Citation Contract (`claims/v1`)

Status: **FROZEN ON LANDING** (unit T-CLAIM-EXIST-01) — this surface is a
proposal until this change merges; once landed, its schema and golden
fixtures are byte-compared by `scripts/generate_claim_citation_contract.py
--check`, and any unexplained change to the contract fails that gate.
Scope: contract only — typed model, JSON Schema, canonical serialization,
golden fixtures, negative regression tests, drift check.
Explicitly out of scope: the citation **resolver/gate** and the
**reporting-path wiring** (see [Deferred](#deferred-to-a-later-unit)).

## 1. Motivation

`docs/architecture/guideline_conformance_and_review_audit_2026-10-21.md` §8.1:
AGRIEVAL's reporting gate passed a meta-analysis that was never executed; its
statistics escaped every gate because they lived in ad-hoc research-layer
scripts *outside* the harness. The first step to preventing that failure
class is a declared, versioned citation contract:

> Every quantitative claim in a report carries a machine-readable citation of
> the form `(artifact_id, path, locator, value)`.

This document freezes exactly that. The gate that resolves citations against
artifacts on disk (requirement 2 of §8.1) and the blocking-finding semantics
(requirements 3–4) are a *later unit built on top of* this contract; mixing
them into this unit would make the contract itself adjustable by gate
convenience, which is the failure mode Contract v1's baseline discipline
exists to prevent.

## 2. The four-field contract

A citation is exactly four fields, enforced by
`ClaimCitation` (`src/scholar_harness/claims/citation.py`) with
`extra="forbid"` — a fifth field such as `confidence` is **rejected at the
model**, not carried as dead state.

| Field | Meaning | Validation (model-level, `strict=True`) |
| :--- | :--- | :--- |
| `artifact_id` | Identity of the backing artifact | Frozen Contract v1 artifact identifier registry: `ART-` prefix + opaque `[A-Za-z0-9][A-Za-z0-9._-]*` suffix (`contracts.identifiers.validate_identifier`) |
| `path` | Where the artifact lives in the workspace | Workspace-relative POSIX path in canonical spelling; see §3 |
| `locator` | Where inside the artifact the value sits | RFC 6901 JSON Pointer, plain string form; see §4 |
| `value` | The value claimed to be present | Canonical-JSON-representable data only; see §5 |

No `value_type` discriminator is added. The JSON type of `value` is already
carried by the value itself, and the comparison rule (§5) is total over
canonical-JSON types, so a discriminator would be redundant state that can
drift from the value it describes. Every other omission from the model is
deliberate: the audit requirement names four fields, and each addition would
be a new thing that can silently disagree with the artifact.

### Why `artifact_id` reuses the v1 registry

A citation whose identity could not bind to a Contract v1
`ArtifactEnvelope.artifact_id` is precisely the "artifact behind the claim"
failure class this surface exists to prevent. Empty, whitespace-only, and
ambiguous-identity strings (`ART-abc def`, `ART-abc/def`, wrong-case prefixes,
non-ASCII suffixes) are therefore rejected **by the model validator**, not
flagged later by a resolver that might be bypassed.

## 3. Path-containment rule

`path` must be a workspace-relative POSIX path in **canonical spelling**. A
citation that escapes the workspace is *invalid*, not merely unresolvable, so
all of the following are rejected by the model:

- empty string (`""`);
- `..` anywhere as a segment (`..`, `../x`, `a/../../b`) — escapes the root;
- absolute paths (`/etc/passwd`, `/`);
- Windows drive prefixes, absolute or drive-relative (`C:/x`, `c:x`);
- backslash separators (`a\b`) — a backslash is ambiguous between a separator
  and a literal character on the Windows host;
- non-canonical spellings that would give one artifact two citation byte
  strings: `.` segments (`a/./b`), redundant separators (`a//b`), trailing
  separator (`a/b/`);
- surrounding whitespace and control characters.

Enforcement: the value must equal `str(PurePosixPath(value))` and pass the
checks above (`citation._validate_citation_path`). This is the same rule
family as the frozen v1 `ArtifactReference.portable_workspace_path`, plus the
canonical-spelling requirement, because citation bytes must be a *function of
the target*, not of how the author typed the path.

## 4. Locator scheme: RFC 6901 JSON Pointer

One scheme, chosen deliberately: **RFC 6901 JSON Pointer in its plain string
form** (e.g. `/results/pooled_effect/risk_ratio`).

Why JSON Pointer over alternatives:

- *Page/line locators* depend on a rendering (of which PDF engine?) and are
  not deterministic across extraction pipelines;
- *regex/verbatim-quote locators* are ambiguous (which match?) and can match
  zero or many positions;
- JSON Pointer is a deterministic, standard, unambiguous function from
  pointer → location in a parsed JSON document, and the artifacts a citation
  may target (`synthesis/*.json`, `phase4/*.json`, ledgers) are JSON.

Validation (`citation._validate_json_pointer`):

- must be non-empty and start with `/` (the empty pointer, which denotes the
  whole document, is not a deterministic single-value locator);
- the `#` URI-fragment form (`#/a/b`) is **not** accepted — one spelling per
  pointer, so two byte-identical citations cannot disagree on form;
- `~` may appear only as part of a `~0`/`~1` escape: `~2`, a dangling `~`,
  and any unescaped `~` are rejected;
- empty tokens (`/`, `/a//b`) remain legal because RFC 6901 defines them.

The deferred resolver must evaluate the pointer per RFC 6901 (single
left-to-right `~1`→`/`, `~0`→`~` decode per token) and treat a pointer that
does not resolve as a **blocking** finding.

## 5. Value-comparison rule (and the number hazard)

`value` is restricted to canonical-JSON-representable data: `null`, `bool`,
`int`, finite `float`, `str`, lists, and string-keyed objects. Functions,
bare objects, sets, bytes, `complex`, `datetime`, `NaN`/`±Infinity`, and
non-string object keys are **rejected at the model** (recursively, at any
depth) — a value that cannot be serialized cannot be verified, and a
verification that would crash must never be constructible as a passing
object.

The comparison rule is **exact structural equality after canonical JSON
serialization**: a claimed value matches an artifact value if and only if

```python
canonical_json_bytes(claimed) == canonical_json_bytes(artifact_value)
```

using the repo's single canonicalizer
`scholar_harness.contracts.canonical.canonical_json_bytes` (sorted keys,
no whitespace, UTF-8, `allow_nan=False`). `json_values_equal()` in
`citation.py` implements exactly this and is the normative comparison.

Number hazard, stated precisely:

- **Integral floats unify with ints**: `1.0`, `1`, and `1.00` have identical
  canonical bytes (`1`) and are therefore *equal*. This matches JSON's
  single-number semantics and the v1 canonicalizer's normalization.
- **`-0.0` unifies with `0`** (INHERITED from the frozen v1 canonicalizer —
  `contracts/canonical.py:53-54`, `if value == 0: return 0` — not a new
  claims-layer decision): `-0.0` and `0` have identical canonical bytes and
  compare *equal*, so a reader is not surprised that the sign on negative
  zero does not change the outcome.
- **Non-integral floats compare by exact binary value**: `1.42` ≠
  `1.4200000000000002`. No epsilon/tolerance is applied at the contract
  level; tolerances are a *gate policy* decision (deferred unit), because a
  hidden tolerance is how a disagreeing value passes a gate.
- **`bool` never equals an `int`**: `true` and `1` are distinct canonical
  bytes even though Python's `True == 1`; the canonical-byte rule is immune
  to Python's bool/int identity hazard.
- **Strings compare exactly** (no case folding, no Unicode normalization);
  **`null` is its own value** (not equal to the string `"null"` or to a
  missing locator).
- `NaN`/`±Infinity` are rejected at the model (canonical JSON rejects them;
  a claim whose value is not even serializable is not verifiable).

### Canonical serialization

`citation_canonical_bytes(citation)` delegates to
`canonical_json_bytes(citation.model_dump(mode="json"))` — the same
function the frozen v1 contract uses. There is exactly **one**
canonicalization in the repo; this unit adds no second one. Two citations
with equal content produce byte-identical canonical bytes regardless of
construction order, dict insertion order, or tuple-vs-list containers
(proved by test, see §8). All generated mappings in serialized output are
key-sorted by the canonicalizer.

## 6. Why a separate versioned surface, not a v1 edit

The Contract v1 baseline (`docs/architecture/contract_v1_baseline.json`,
enforced by `scripts/generate_contract_baseline.py --check`) locks the hash of
every file under `src/scholar_harness/contracts/*.py` and every schema in
`SCHEMA_MODELS`. Registering `ClaimCitation` there would move the frozen
baseline, and the audit requirement (a *citation of a report claim*) is a
different concern from the v1 artifact-acceptance envelope: it must be
adoptable by the reporting path without re-opening the v1 adoption program.
Therefore:

- new package `src/scholar_harness/claims/` — additive, owns nothing under
  `contracts/`;
- own schema base URI: `https://nexus-scholar.org/schemas/claims/v1`
  (v1 remains `https://nexus-scholar.org/schemas/contracts/v1`);
- `SCHEMA_MODELS` of the frozen catalog is untouched; a test asserts no v1
  catalog entry is this model;
- the surface *reuses* v1's canonicalizer and identifier registry by import,
  so identity and canonical-JSON semantics cannot drift between surfaces.

## 7. Frozen-and-checkable: the drift check

`scripts/generate_claim_citation_contract.py --check` regenerates, in memory,
every derived artifact of this contract and byte-compares against the
committed files:

- `src/scholar_harness/claims/schemas/claim-citation.schema.json` (JSON
  Schema, draft 2020-12, `$id` under the claims/v1 base URI);
- `tests/fixtures/claim_citation/valid_citation.json` + the exact golden
  canonical bytes `valid_citation.canonical.json`;
- `value_shifted_citation.*` — differs from the valid citation **only** in
  `value` (1.42 → 1.43); its canonical bytes MUST differ;
- `locator_shifted_citation.*` — differs **only** in one locator token; its
  canonical bytes MUST differ.

Because every fixture is *derived from the live model*, any unexplained
change to the validators, the field set, or the canonicalization changes the
derived bytes and fails `--check` until explicitly regenerated and reviewed —
the same discipline as `generate_contract_schemas.py --check` for v1. A
fixture that the contract no longer accepts fails `--check` with an explicit
message rather than being silently dropped. Because a *weakened* validator
need not move any derived byte, `--check` additionally re-runs a fixed table
of 20 must-reject inputs (escaping paths, malformed pointers — missing `/`,
bad escapes, dangling `~`, fragment form, empty — ambiguous `artifact_id`s,
non-finite/unverifiable values, a fifth field) through the live model and
fails if any becomes acceptable. Unexpected extra files in either generated
directory also fail `--check`.

**Which artifact is authoritative.** The generated JSON Schema is
**STRUCTURAL** only: it fixes the field names, the four-field shape, and
`additionalProperties: false`, but it cannot express the semantic
validators — its `path`, `locator`, and `artifact_id` properties are bare
`"type": "string"`, so schema-only validation would accept
`{"path": "../x"}`. The pydantic model validators are **NORMATIVE**: a
non-Python consumer MUST also implement the prose rules in §§3–5 (path
containment, RFC 6901 pointer form, canonical-JSON value kinds) — schema
validation alone is insufficient to reject an escaping path. This mirrors
the frozen v1 convention, where `contracts/models.py:155-157` enforces
`portable_workspace_path` in Python while the v1 JSON Schemas likewise
carry no `pattern`; the structural/normative split is deliberate and
consistent across both surfaces.

## 8. Acceptance map

| # | Requirement | Where proved |
| :--- | :--- | :--- |
| 1 | Citation is exactly `(artifact_id, path, locator, value)` | `ClaimCitation` + `ConfigDict(extra="forbid")` in `src/scholar_harness/claims/citation.py`; tests `test_extra_field_is_rejected_at_the_model`, `test_missing_field_is_rejected_at_the_model` |
| 2 | No unjustified extra fields; no `value_type` | Module docstring of `citation.py` ("Design decisions"); schema `additionalProperties: false` asserted in `test_claims_surface_is_registered_under_its_own_base_uri` |
| 3 | `path` cannot escape the workspace (model-level) | `citation._validate_citation_path`; tests `test_path_is_rejected_at_the_model` (16 cases: `..`, absolute, drive, backslash, empty, `.`, non-canonical spellings, whitespace, control chars) and `test_path_accepts_workspace_relative_posix_forms` |
| 4 | `locator` is one validated scheme (RFC 6901) | `citation._validate_json_pointer`; tests `test_locator_is_rejected_at_the_model` (missing `/`, `~2`, unescaped `~`, fragment form, empty) and `test_locator_accepts_rfc6901_pointers` |
| 5 | `value` comparison rule incl. number hazard | `json_values_equal` + module docstring; tests `test_integral_float_unifies_with_int`, `test_boolean_never_equals_int`, `test_numbers_do_not_coerce_to_strings`, `test_non_integral_floats_compare_exactly_without_tolerance`, `test_structural_equality_over_nested_values` |
| 6 | Unverifiable value kinds rejected at the model | `citation._validate_json_value`; test `test_value_is_rejected_at_the_model` (NaN/inf, set, bytes, complex, datetime, object, function, non-string keys — nested too) |
| 7 | Canonical serialization reuses the repo convention (one canonicalizer) | `citation_canonical_bytes` → `contracts.canonical.canonical_json_bytes`; golden test `test_canonical_bytes_match_golden_fixture` |
| 8 | Determinism proven, not asserted | Tests `test_canonicalization_is_deterministic_across_calls_and_instances` (serialization path run 4× in-test) and `test_canonicalization_is_content_based_not_identity_based` (rekeyed dict / kwargs constructions → identical bytes) |
| 9 | Byte difference is forced by content difference | Tests `test_value_shift_must_change_canonical_bytes`, `test_locator_shift_must_change_canonical_bytes` (+ their golden `.canonical.json` fixtures) |
| 10 | Separate versioned surface; frozen v1 untouched | `schema_catalog.py` (claims/v1 base URI); tests `test_claims_surface_is_registered_under_its_own_base_uri`, `test_frozen_v1_catalog_is_untouched_by_the_claims_surface`; plus the four unchanged v1 frozen `--check` commands in §9 |
| 11 | Contract frozen-and-checkable | `scripts/generate_claim_citation_contract.py --check`; test `test_bundled_schema_file_matches_the_renderer` |
| 12 | `artifact_id` closed under negative testing | Tests `test_artifact_id_is_rejected_at_the_model` (empty, whitespace-only, empty suffix, ambiguous chars, wrong/missing prefix, non-ASCII) |
| 13 | No new dependencies | Validation §9: `git diff --stat pyproject.toml uv.lock` empty; imports limited to stdlib + pydantic + frozen v1 contract modules |

## 9. Validation

Run in the worktree at `c2b1ed2` + this unit:

```
uv run pytest tests/unit/test_claim_citation_contract.py -q -o addopts=""
uv run python scripts/generate_claim_citation_contract.py --check
uv run python scripts/generate_contract_baseline.py --check
uv run python scripts/generate_contract_schemas.py --check
uv run python scripts/generate_two_study_contract_fixture.py --check
uv run python scripts/generate_nexus_scholar_pins.py --check
uv run ruff check scripts/
git diff --stat pyproject.toml uv.lock
```

## 10. Deferred to a later unit

Deliberately **not** in this unit (safe to defer: none of them can weaken the
contract, and none are implied by it):

1. **The resolver/gate** — reading the artifact at `path`, evaluating the
   JSON Pointer, comparing `value` with `json_values_equal`, and turning a
   miss into a *blocking* finding (audit §8.1 requirements 2–3). It must be
   built *against* this frozen surface, not folded into it.
2. **Reporting-path wiring** (audit §8.1 requirement 4) — enforcing that
   report generation emits and checks citations (audit §8.3 priority 1).
3. **Tolerance policy** for non-integral floats — explicitly excluded here
   (§5); a gate may never silently widen the comparison rule.
4. **Artifact-content binding** (pinning `artifact_id` to a `sha256` of the
   artifact bytes) — belongs with the resolver, which must verify the
   artifact on disk did not change between citation and check.
5. **The statistical layer's home** (new `scholar-stats-kit` vs extending an
   existing kit, audit §8.1 decision table) — an ownership/dependency
   decision orthogonal to this contract; nothing here adds a dependency.

## Toolkit sync / workspace audit

None: this unit touches only `src/scholar_harness/` (harness owner surface),
`tests/`, `scripts/`, and `docs/`. No kit source under `tools/` is modified,
no pin in `plugins.json` changes, and no workspace is mutated.
