# Charting limitation F1 — repair design (DRAFT, NOT FROZEN)

**Status:** design proposal for researcher review and a new freeze. The frozen
`charting.schema.json` (`02eaf2ce…ace85`) is unchanged, and **no charting row may
be accepted** under this draft until it is reviewed, frozen, and its hash
recorded.

## The defect (as recorded at freeze)

From `validation.json`:

> v0.3 draft charting schema does NOT couple `evidence_state` to content: a row
> with `evidence_state=not_reported` and fully populated values/provenance
> validates. The pilot v0.2 sidecar enforces state→value/evidence/note
> conditional invariants.

Concretely, this is valid under v0.3 today:

```json
{
  "uncertainty_calibration": {
    "evidence_state": "not_reported",
    "uncertainty_method": "deep_ensemble_variance",
    "calibration_metrics_reported": ["ECE", "Brier_score"],
    "narrative_summary": "Authors omit calibration.",
    "provenance": { "verbatim_quote": "…", "locator": "Table 4" }
  }
}
```

The dimension says "not reported" and simultaneously supplies a method, metrics
and a supporting quote. That is not a schema nuisance: it lets a charted cell
claim absence while asserting content, and it makes `not_reported`,
`unavailable`, `not_applicable` and `conflicting` interchangeable in practice.

## Repair principle

`evidence_state` is the claim; **content and provenance are its evidence**. For
every dimension block:

| state | content must be | provenance must be |
| :--- | :--- | :--- |
| `reported` | the reported value(s); no nulls for the dimension's primary fields | ≥1 anchor with a verbatim quote that supports the value |
| `not_reported` | empty (nulls / empty arrays / null booleans), nothing inferred | 1 anchor quoting the explicit absence check, e.g. `[Checked §2–3: no split unit stated]` |
| `unavailable` | empty | 1 anchor naming why (paywall, missing supplement), not a content quote |
| `not_applicable` | empty | 1 anchor quoting why the dimension does not apply |
| `conflicting` | empty (no single value may be asserted) | ≥2 anchors with mutually inconsistent quotes |

Two consequences that are deliberate:

- **`false` is not "unknown".** `funding_and_coi_disclosed: false` means
  *reported: no disclosure*; `not_reported` means *we cannot tell*. The boolean
  fields that can be unknown become tri-state (`true | false | null`).
- **`not_reported` must leave the dimension's value fields empty.** A value that
  is itself the string `not_reported` (e.g. `agricultural_setting:
  "not_reported"`, `stress_origin: "not_reported"`) is the same conflation and
  is removed from the enums in favour of the dimension state.

## Proposed changes to `charting.schema.json` (v0.3.1)

### 1. `provenance_anchor` gains a state-aware shape

Keep the current object but require the quote to be non-empty in all states
(it already is, `minLength: 5`), and add `absence_check: boolean` so an
absence-quote is distinguishable from a content-quote. `reported` requires
`absence_check: false`; `not_reported | unavailable | not_applicable` requires
`absence_check: true`.

### 2. `conflicting` needs more than one anchor

Add `additional_provenance: [provenance_anchor]` (minItems 1) to every
dimension block, allowed only when `evidence_state == "conflicting"`, and
required then. Without it, `conflicting` cannot show what conflicts.

### 3. Per-dimension conditional shapes

Add `allOf` to each of the 13 dimension blocks. The table below is the
proposal; the "empty" columns are what `not_reported | unavailable |
not_applicable` must satisfy.

| Dimension | Primary value fields (held empty when not reported) | Notes |
| :--- | :--- | :--- |
| `study_reports` | `primary_report_doi: null`, `linked_reports: []`, `primary_publication_year: null` | publication type may stay (it is bibliographic, not a finding) |
| `task_context` | `crop_species: []`; `agricultural_setting`, `weed_granularity`, `vision_task`, `uav_separability` → `null` | remove `not_reported` from `agricultural_setting` enum |
| `dataset_units` | `dataset_names: []`, all `*_count: null`; `dataset_origin`, `independent_unit_level` → `null` | |
| `sensor_inputs` | `modalities_used: []`, `spectral_bands: []`, `derived_indices_used: []`; `gsd`, `altitude`, `radiometric_calibration` → `null` | |
| `availability_alignment` | `stress_categories_evaluated: []`; `stress_origin`, `alignment_or_restoration_method` → `null` | remove `not_reported`/`not_applicable` from `stress_origin` enum; use the dimension state |
| `temporal_design` | `temporal_regime` → `null`, `crop_growth_stages_bbch: null` | |
| `split_protocol` | `partition_unit`, `spatial_leakage_risk`, `target_domain_data_use` → `null` | |
| `fusion_mechanism` | `architecture_family`, `integration_topology` → `null`; `matched_modality_ablation_present: null` | boolean becomes tri-state |
| `uncertainty_calibration` | `uncertainty_method` → `null`, `calibration_metrics_reported: []`, `abstention_or_validity_rejection: null`, `false_calibration_terminology_trap` → `null` | |
| `metrics_comparators` | every `primary_metrics.*` → `null`; `weed_class_specific_metrics_reported: null`, `variance_or_ci_reported: null`, `repeated_seeds_or_folds_count: null` | |
| `transfer_outcomes` | `shift_axes_tested: []`, `adaptation_regime` → `null`, both metric values and delta → `null`, `failed_transfer_documented: null` | |
| `provenance_limits` | `missing_or_ambiguous_dimensions: []`, `internal_contradictions_noted: null`, `claimed_vs_demonstrated_gap` → `null` | |
| `open_science` | `data_availability`, `code_availability`, `license`, `retraction_or_correction_status` → `null`, `funding_and_coi_disclosed: null` | careful: `not_reported` ≠ "not available" |

`narrative_summary` stays required in every state and must explain the absence.

### 4. Enums that must stop encoding absence

- `task_context.agricultural_setting`: drop `not_reported`.
- `availability_alignment.stress_origin`: drop `not_reported` and
  `not_applicable` (the dimension state carries them).
- `open_science.data_availability` / `code_availability`: keep `not_reported`
  **only if** it means "the paper reports that availability is not stated" —
  otherwise it duplicates the dimension state. Decision requested below.

## Why a conditional schema rather than a validator script

The v0.2 sidecar proved the logic; the loss here came from re-expressing the
cells as typed objects without carrying the invariants across. A JSON-Schema
`allOf`/`if`/`then` keeps the rule in the same artifact as the shape, so a
future edit cannot drop it as easily as a separate script can. If the
conditionals become unreadable, the fallback is a post-schema validator that
returns named refusals per dimension — but then the schema alone no longer
means "valid row".

## Negative test matrix (must all refuse before freeze)

1. `not_reported` + populated value in each of the 13 dimensions (13 rows).
2. `not_reported` + `provenance.absence_check: false` or a content quote.
3. `reported` + a null primary field.
4. `reported` + empty `provenance_anchor`.
5. `unavailable` with a value.
6. `not_applicable` with a value, and with a "reported" rationale.
7. `conflicting` with one anchor; with zero anchors.
8. `conflicting` + a single asserted value.
9. `false` used where `null` is required (six boolean fields).
10. A row that validates under v0.3.0 but must fail under v0.3.1 — kept as a
    regression fixture.

Positive matrix: the v0.2 pilot sidecar rows (or a faithful subset) must still
validate after translation, with `state → evidence_state` and `cell.value`
→ the dimension's primary field. This is the strongest evidence that the repair
imports the old logic rather than inventing a new one.

## Migration and freeze

- **No charting rows were accepted** under v0.3 (`validation.json`), so there is
  no data migration. The draft is replaced, not repaired in place.
- Bump the schema to v0.3.1, record the new sha256 in `project.json`
  (`charting_schema_sha256`), `AMENDMENTS.md` and `validation.json`, and state
  that F1 is **repaired** rather than accepted.
- `protocol.json` and the criteria are untouched: charting is a separate
  instrument and its hash is recorded separately.
- `CHARTING_CODEBOOK.md` needs one new section defining the five states and the
  "empty shape" rule, with two worked examples (`not_reported` vs
  `not_applicable`, and a `conflicting` row with two quotes).
- After the freeze, re-run the codebook rows that were written against v0.3.0 to
  confirm they still parse.

## Open decisions for the researcher

1. **Boolean tri-state:** accept `null` for the six boolean fields, or split each
   into a separate `*_state`? (Recommend `null`; fewer fields.)
2. **`open_science` enums:** drop `not_reported` from `data_availability` /
   `code_availability`, or keep it as "paper states availability is not
   described"? Keeping it makes "not reported" expressible at value level *and*
   state level — the exact ambiguity F1 is about. Recommend dropping.
3. **`conflicting` anchoring:** is two quotes enough, or does a conflict require
   a third adjudicating note? (Recommend two anchors + required
   `narrative_summary` describing the conflict.)
4. **Strictness for `primary_publication_type`:** keep it required even when the
   report is `not_reported`, or null it too?

## Verification once frozen

- Every negative case above refuses with the schema's own error, and the
  positive v0.2 translation passes.
- `generate_contract_baseline.py --check` (charting is not a Contract-v1 frozen
  payload, but the gate must stay green).
- The new hash is recorded everywhere the old one appears; a grep for
  `02eaf2ce` returns only historical references marked superseded.
