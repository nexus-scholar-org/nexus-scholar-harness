# M10c-critic-test-set: a test set of broken protocols for the M10c critic
Branch: dev/m10c/critic-test-set · Lane: **STANDARD** (tests, fixtures and documentation only) · Status: READY FOR REVIEW, not pushed · Started: 2026-11-18

Source: `docs/roadmap/production-plan.md` §6, row **M10c-assistant-mcp**: "an assistant and a critic over MCP … with a test set of deliberately broken protocols the critic must catch". The researcher approved this preparation on 2026-11-18. M10c itself cannot start until M10b (the proposal object and the 51 fixed, non-AI checks) is built; M10b is being built in another session. This milestone prepares only the test set, so M10c can start with it. It is not the first step of M10c and it does not decide M10c's design.

**Lane.** STANDARD, from `docs/architecture/test_gate_policy.md`: new fixtures, one new test file and documentation; no change under `src/`, `apps/` or `docs/ux`, no public API, CLI or MCP behaviour, no Contract v1 model, schema or golden fixture. The baseline check runs anyway (below).

## What was built
`tests/fixtures/critic_protocols/` (all new):

- two sound bases, each as an `IntentPacket` and as its compiled `protocol.json`: a **scoping review** (UAV crop-weed mapping, how studies evaluate generalization; derived from the golden UAV workspace, simplified) and a **systematic review** (UAV-guided versus uniform herbicide application, comparative field trials, meta-analysis);
- 40 variants (26 from the scoping base, 14 from the systematic one), 43 defects: 37 variants with one defect, 3 with two that interact. 5 critical, 29 major, 9 minor. **31 of the 43 defects are "none: critic only"**: no existing validation and no fixed check of `02-checks.md` can see them;
- `manifest.json` (`critic-protocols-v1`): per variant its base, format, exact differing fields, existing-validation result, and per defect the sentence, fields, severity, category, catching fixed check (or `none: critic only`) and the finding a good critic must report; the 51 check ids of the catalogue; a seed catalogue;
- `README.md`: how M10c scores a critic (caught, missed, false alarms on the two bases) and what the set does not cover.

And `tests/kits/protocol/test_critic_protocol_set.py` (about 170 test cases), which proves the set is honest today with no model: every fixture loads and the manifest and the folder agree; both bases compile and validate with no error and no warning, and the checked-in compiled protocol and the manifest fingerprint equal what the compiler produces; each variant differs from its base exactly in the fields the manifest names; every `accepted_locators` pointer exists; the assignments to fixed checks are pinned in the test; and the manifest's statement of what existing validation rejects is what the real compiler and `validate_protocol` do. It does not test the fixed checks (their code is in M10b).

## Definition of done
- [x] **D1 Sound bases.** One scoping and one systematic protocol in the repository's own format, compiling cleanly. `test_base_compiles_cleanly`, `test_base_seeds_are_real_records_the_criteria_keep`.
- [x] **D2 Variants.** 40 variants, one defect each, four with two. Every class the brief names has at least one (`test_the_set_shows_what_the_fixed_checks_cannot_see` asserts the classes).
- [x] **D3 Additions from the specs.** Defects found in `02-checks.md` and in the compiler, validator and search adapter that the brief's list misses: see the README, "Where each defect class comes from". `03-guidance.md` is a set of screen-copy rules and describes no protocol defect.
- [x] **D4 Manifest.** Every field the brief asks for, per defect (the unit a critic is scored on). The fixed-check assignments are hand-traced; `check_certainty` says when the trace is partial.
- [x] **D5 Honesty test.** `tests/kits/protocol/test_critic_protocol_set.py`.
- [x] **D6 README.** Scoring and limits.
- [ ] **D7 Gates and review**, recorded below. The independent review returned CHANGES on the first pass; the repairs are listed under "Review round 1".

## Decisions taken here (the researcher may overrule; none touches a contract)
1. **The unit is the defect, not the variant.** The manifest keeps `defects[]` per variant (one entry, or two for an interacting variant), each with its own severity, check and finding. The brief lists these keys per variant; for the 36 single-defect variants the list has one entry. An interacting variant is scored per defect.
2. **Two artefact forms.** Variants are `IntentPacket` files (the authored input, and what an inception draft compiles to through `build_intent`). Only two defects exist solely in a compiled protocol (criterion ids are generated, so a duplicate or case-colliding id cannot be written at intent level); those two variants are in `protocol` format and derive from the compiled base. Which artefact the M10c critic reads is left to M10c.
3. **"Rejected by existing validation" has two layers.** `compile_protocol` rejects an intent that the `IntentPacket` model refuses (`intent_model`); the cross-field rules (`CROSS_FIELD_RQ_REF`, `DATE_RANGE_INCOHERENT`, `DUPLICATE_CRITERION_ID`, `POOL_SIZE_INCOHERENT`) live in `validate_protocol`, which `compile_intent` and the inception preview do not call. The manifest records both (`rejected_by`: `intent_model`, `compile`, `validate_protocol`, or null) and the warning codes. Four variants are rejected; this shows what the existing checks cover and leaves the other 36 compiling cleanly.
4. **Seeds are real.** Recall seeds are DOIs from `workspaces/golden-uav-30/literature/verified.json` with their titles and years in `seed_catalog`; the set invents no DOI. The systematic base therefore has no seeds (no verified comparative-spraying trial exists in the repository); the README says a critic may note this but not raise it as a major finding.
5. **The fixed checks are not on `main` yet.** `02-checks.md` is read from `dev/m10b/proposals-checks` at `2d07228d`; the 51 ids are copied into the manifest. When M10b is built, its checks should be run over the 42 documents and the manifest corrected where the code disagrees.
6. **Scoring bars are suggestions.** The README proposes (every critical caught; 80% of critic-only majors; no major false alarm on either base). They are for M10c and the researcher to fix.

## Review round 1 (`milestone-reviewer`, Sonnet): CHANGES, repaired
Checked defect by defect against the variant files. Repairs made, none contested:
1. `sr-no-control-arm-requirement` still left a comparator in two other criteria; the systematic base is rewritten (INC-01 intervention and arable setting, INC-02 design with control arm, INC-03 date and language) so the variant now removes the only requirement.
2. The base selected on reported outcomes (a recognised bias), which made `sr-outcome-not-required` and its chain contested: the base criterion is gone, `sr-outcome-not-required` is dropped, and the chain becomes `sr-matrix-misses-rq2-outcomes` (the extraction form has no column for RQ2's outcomes).
3. The scoping base omits the word generalization from the search; this is now stated as deliberate in its rationale and in `base_notes`, so `scoping-outcome-term-in-query` is a defect of the variant, not of the base (the generic synonym `transfer` was removed).
4. The systematic base's third concept listed the comparator as synonyms of "field trial": renamed and cleaned.
5. Each defect has `accepted_locators` (the other half of a contradiction, the field an edit conflicts with); the README scoring rule and a test use them. Before, a critic naming the other half of a pair would have been scored a miss.
6. Regraded: the two "search omits a concept" defects are major (not critical); the planned-size defects are minor (the size is advisory); `scoping-phantom-rq-reference` is major (the validator treats it as an error); the empty unit of analysis and the missing exclusion side are major (tool blockers are not methodology grades).
7. `sr-planned-size-left-to-preset` no longer claims a disproportion; tool-rule and hygiene defects are named in the README and kept out of the suggested bars; a variant for two exclusions repeating each other (`scoping-duplicate-exclusion-different-reasons`) covers "overlapping criteria".
8. `check_certainty` for the weed-concept variant is "uncertain, may not fire" (tokenisation of `crop-weed` is not specified); `HARVEST_ABOVE_TARGET` added to the planned-size variants; the README states that fixed checks will not be silent on the bases (`CONCEPT_TERM_MISSING` is a warning; `DIRECTION_SEEDS_FEW` fires on the systematic base) and that the missing start year is visible as null.
9. Tests: `test_most_variants_compile` replaced by a bound on what the compiler refuses; the fixed-check assignments are pinned in the test.
Left as the reviewer noted, not changed: the context-missing variant is moderate (an agricultural setting is implied by "crop and weed mapping"); the single-seed rule is a tool threshold (marked as such).

## Findings that matter for M10c
- The planned pool size is advisory and never caps retrieval (`protocol_adapter.py`, SRCH-31), so a too-small planned size is a planning inconsistency, not a cut; the variants say so.
- `boolean_operator: "AND"` on a concept is honoured by the search adapter and makes a near-empty query; nothing checks it (`scoping-synonyms-joined-by-and`).
- One defect is invisible in the compiled protocol (a preset fills a size nobody chose): a critic given only `protocol.json` cannot see it. A missing start year shows as `start_year: null`. M10c must choose its input.
- `validate_protocol` is not called on the inception path; `REVIEW_COMPILER_REFUSED` (compile only) would not see a criterion that cites a question that does not exist. Worth a decision in M10b or M10c, outside this milestone.

## Evidence
Base for every selection: `origin/main` at `e7644a6c`.

| Stage | Command | Result |
| :-- | :-- | :-- |
| inner | `uv run --extra dev pytest tests/kits/protocol/test_critic_protocol_set.py` | all passed |
| selection | `uv run python scripts/select_test_gate.py --changed origin/main --stage pr` | `git diff --check`, **`uv run pytest -q -n auto`** (the full suite), `ruff check scripts/`. Not the small selection the brief expected: the selector has no area for a new test file and falls back to the full suite (`select_test_gate.py`, `area_defaults`/`fallback`). Run once with 3 workers because the machine was busy. |
| gate | see below | see below |
| contract baseline | `uv run python scripts/generate_contract_baseline.py --check` | current |
| lint | `uv run ruff check scripts/`; `uv run ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9`; the new test file | all passed |
| whitespace | `git diff --check origin/main` | clean |
| review | `milestone-reviewer` | see below |
