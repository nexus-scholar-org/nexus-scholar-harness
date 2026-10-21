# Screening decision contract fixtures (T-D0D2)

Static, hand-authored fixtures for
`src/scholar_harness/screening/decision_contract.py`.  Nothing here is
generated; the files are the reviewed inputs of the new test module.

## Layout

| Path | Use |
|---|---|
| `contracts/agent_lane.json` | The standard agent screening-lane contract: canonical fields, allowed extras, the four alias classes, the decision vocabulary, the embedded reason-code pattern, and **no** expected instrument SHA prefixes. |
| `contracts/agent_lane_with_sha.json` | The same contract with `expected_criteria_sha256_prefix` / `expected_prompt_sha256_prefix` configured, so instrument attestation is exercised. |
| `contracts/unsupported_major.json` | The same contract with `schema_version` `"2"` (an unsupported major). |
| `parents/batch_0001.json` | Parent batch manifest: `n_records`, the attested instrument SHAs, and the record list. |
| `parents/batch_0001.view.json` | Parent view: the authoritative id order. |
| `scenarios/<name>/` | One scenario per directory.  Files named `batch_0001.json` or `batch_0001.view.json` override the shared parents; every other file is the decision file under test. |

The test helper copies the shared parents first and then the scenario
directory over them, so a scenario only has to carry what it changes.

## Scenarios

`canonical`, `alias_exclusion_reason_code`, `alias_pending_reason_code`,
`alias_inclusion_hint`, `alias_reason_CODE`, `missing_confidence`,
`non_numeric_confidence`, `out_of_range_confidence`,
`rationale_in_reason_only`, `absent_reason_code`, `embedded_reason_code`,
`unknown_keys`, `no_canonical_field`, `header_unattested`,
`missing_screener_id`, `missing_instrument`, `row_count_mismatch`,
`id_order_mismatch`, `wrong_workspace_ids`, `missing_screening_id`,
`empty_screening_id`, `decision_out_of_vocab`, `non_canonical_filename`,
`bom_prefixed`, `malformed_json`, `missing_parent`, `stale_instrument`,
`prompt_count_mismatch`.

`missing_parent` intentionally ships **no** parent override: the test helper
is told not to copy the shared parents for that scenario, so both the batch
manifest and the view are absent.

`missing_instrument` overrides both parents with copies that carry **no**
instrument SHA, so the instrument cannot be attested at all while a prefix is
configured.
