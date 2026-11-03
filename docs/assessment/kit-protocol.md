# scholar-protocol-kit assessment — 2026-11-03

Status: independent assessment, read-only. Commit 5deb3a1 (vendored `tools/scholar-protocol-kit`). Scope: `tools/scholar-protocol-kit/src/scholar_protocol/` (11 modules, 2,375 lines by `wc -l`), `tests/` (7 test modules, about 1,350 lines, plus 17 JSON fixtures), `schemas/v1/protocol.schema.json`, `scripts/generate_schema.py`. Harness consumers: `src/scholar_harness/` grep for `scholar_protocol`. Method: read every source module in full. Ran `uv run pytest tools/scholar-protocol-kit/tests` (144 passed, 4 warnings, 52.7 s). Ran two offline repro scripts against the shared `.venv` (scratchpad `prot_repro.py`; results quoted inline as R1–R13). Grepped every `tools/*/src`, `src/scholar_harness`, `.agents` and `apps` for consumers of the protocol fields. Docs (README, SKILL.md, `docs/kits_surface_matrix.md`) were treated as claims to check, not as evidence.

## 1. Verdict

The kit does a narrow job well. It defines a typed `ResearchProtocol`, compiles an `IntentPacket` deterministically, and pins byte-level fingerprints with golden fixtures. Within that scope the tests are good. It does not do the job its name implies: holding a systematic-review protocol a researcher could register or defend. Several things the protocol and `SCREENING_CRITERIA.md` declare are not enforced by any code in the repo: the trust-score inclusion threshold, the verification flags and `incompatible_concepts` (PROT-01). The compile path writes `protocol.json` without running the kit's own cross-field rules, so the harness can persist a protocol whose criteria cite non-existent RQs or whose dates run backwards (PROT-02). Unknown or misspelled keys are silently dropped and leave the fingerprint unchanged, which defeats the "protocol amendment changes the fingerprint" guarantee (PROT-03). The model has no fields for most PRISMA-P items: registration, amendments, selection process (number of reviewers, conflict resolution), risk-of-bias tool, synthesis plan, and certainty of evidence. Its `prisma-check` scores against an invented 20-item list, not PRISMA 2020.

| Lens | Rating | Reason |
|---|---|---|
| Code quality & architecture | Adequate | Pure compiler, golden fingerprints and a schema-sync test. But it is stringly typed, the intent and protocol models are duplicated field by field, the cross-field validator is private yet imported by another kit, and the runtime model is laxer than its own JSON Schema. |
| Correctness & bugs | Weak | The canonicalization holds for the fixtures. Real gaps: silent key dropping, a non-deterministic `created_at` default, compile without cross-field validation, and an extraction model that crashes or mis-types some dimension ids. |
| Research-method fitness | Weak | It covers RQs, eligibility text, databases and data items. It lacks the PRISMA-P essentials (selection process, RoB, synthesis, amendments and versioning), uses a trust-score exclusion gate that nothing enforces, and mislabels its own checklist as PRISMA 2020. |

## 2. Architecture and code quality

**What is solid.** `compile_protocol` is a pure function with no I/O (`compiler.py:126-240`). Every golden intent compiles to its pinned `.sha256` (`tests/test_compiler.py:68`). A test checks that the JSON Schema stays in sync with the models (`tests/test_schema_sync.py:61`). ID generation (RQn, INC-nn, EXC-nn) is frozen and tested. These properties are worth keeping.

**Stringly typed core concepts.** Fields that steer downstream behaviour are free `str`, so any value passes validation:
- `ConceptCluster.boolean_operator` (`models.py:113`): "XOR" is accepted (R8c).
- `ScreeningCriterion.reason_category` (`models.py:163`): screening exclusion reasons are not a controlled vocabulary, so PRISMA flow counts cannot be aggregated reliably.
- `ResearchQuestion.synthesis_type` (`models.py:93`).
- `MatrixDimension.target_section_category`, whose docstring lists four allowed values that are never enforced (`models.py:212-218`).
- `EpistemologyConfig.trustworthiness_framework` (`models.py:250`).

`date_range` and `target_candidate_pool_size` are bare `Dict`s (`models.py:130,142`). They are not sub-models, so the keys are not validated (R8b: `{"from": 2030, "to": 1900}` passes with zero findings). The canonicalizer then has to special-case their key order (`canonical.py:67-78`).

**Duplicated model layer.** `intent.py` re-declares near-copies of `ResearchQuestion`, `ConceptCluster`, `ScreeningCriterion` and `MatrixDimension` (`intent.py:48-118`). The compiler copies them field by field (`compiler.py:65-118`), builds sub-models, dumps them to dicts and re-validates the whole thing (`compiler.py:226-240`). Adding a protocol field means editing four places. `golden_seeds` was already missed this way (PROT-10).

**The runtime model is laxer than the schema it claims to generate.** `models.py:3-5` calls the model "the *sole* runtime source of truth" and says the JSON Schema is derived from it. `scripts/generate_schema.py:22,75-87` post-processes the schema to add `additionalProperties: false` everywhere except `metadata`. No model sets `extra="forbid"`; every `model_config` uses only `populate_by_name=True`, e.g. `models.py:303`. The schema and the runtime therefore disagree on what a valid file is (PROT-03).

**Private validator used as a public API.** The cross-field checks live in `_check_cross_field` (`validate.py:122`). The only public entry point is the path-based `validate_protocol` (`validate.py:382`), so there is no public way to validate an in-memory model. `tools/scholar-agent-kit/src/scholar_agent/server.py:63,273` imports the private function. Meanwhile `compile_protocol` and the harness skip it entirely (PROT-02).

**Smaller issues.**
- Function-local imports: `validate.py:179` imports `datetime` inside the rule body, and `validate.py:240` imports enums the module could import at the top.
- `canonical.py:125-129` describes a "post-process float representation" step that does not exist. The comment documents dead behaviour.
- Models are mutable (not `frozen`), so a `ResearchProtocol` can change after it has been fingerprinted.
- `presets.py` shares one `_DEFAULT_DATABASES` list object across all five frozen presets (`presets.py:38-43,74,89,104,119,134`). The compiler copies it (`compiler.py:190`), so this is latent rather than live.
- The CLI catches bare `Exception` and exits 2 (`cli.py:83-90,186-190`), which turns compiler bugs into "usage error".

**Tests.** 144 tests, all passing. They are strong on canonical bytes, fixtures, structural enums and CLI exit codes. They have three gaps:
- There are no unit tests for `render.py` or `extraction.py`. The only coverage is three CLI smoke assertions (`tests/test_cli.py:210-253`), which do not check that criteria meaning survives or that the extraction schema is right.
- No adversarial canonicalization tests (Unicode, nested metadata, timestamp forms).
- On Windows, `tests/test_cli.py:39` runs the CLI with `text=True` under the cp1252 locale, while the CLI forces UTF-8 output (`cli.py:59-65`). Four subprocess reader threads raise `UnicodeDecodeError` (pytest `PytestUnhandledThreadExceptionWarning` in `test_validate_*`). Those tests pass only because they assert exit codes, not output (PROT-12).

## 3. Correctness and bugs

**PROT-01 — High — Static (exhaustive grep).** Protocol safeguards are declared and rendered but never enforced.
- **Evidence:** `VerificationConfig` (`models.py:264-286`) holds `retraction_check_required`, `coi_and_funding_audit_required`, `reproducibility_das_cas_check` and `minimum_trust_score_threshold` ("Minimum Phase 4 trust score … for a paper to be included"). `EpistemologyConfig.incompatible_concepts` is described as "Terms suppressed from search / synthesis" (`models.py:258-261`). I grepped every `tools/scholar-*-kit/src`, `src/scholar_harness`, `.agents` and `apps`. These names occur only inside scholar-protocol-kit and in the harness *producer* `src/scholar_harness/inception/intent.py:276,300-304`, which writes them. Nothing reads them. Even so, `render.py:76-87` prints "- [x] Retraction check required … Minimum Trust Score: 6.0" into `SCREENING_CRITERIA.md`, the document handed to the screener. The inception wizard asks the researcher for a `trust_score_threshold` (`intent.py:304`) that has no effect.
- **Impact:** The protocol says studies below the trust threshold are excluded and that suppressed terms are suppressed. A methods section that repeats this would describe safeguards that never ran.

**PROT-02 — High — Reproduced (R9).** The compile path persists incoherent protocols.
- **Evidence:** `compile_protocol` returns after Pydantic structural validation only (`compiler.py:240`). It never calls `_check_cross_field`. The harness genesis path writes the result straight to disk, with no validation: `src/scholar_harness/inception/genesis.py:162-166` writes `protocol.json` and `SCREENING_CRITERIA.md`, and no call to `validate_protocol` or `_check_cross_field` exists anywhere in `src/scholar_harness`. Repro: I compiled `prisma_slr_full.intent.json` with `maps_to_rqs=["RQ99"]`, `start_year=2030` and `end_year=1990`. It compiled successfully. Running the kit's own cross-field check on the output then reports `['CROSS_FIELD_RQ_REF', 'DATE_RANGE_INCOHERENT']`.
- **Impact:** A fingerprinted genesis protocol can be internally contradictory. Every downstream artifact then binds to that fingerprint.

**PROT-03 — High — Reproduced (R6).** Unknown or misspelled keys are silently dropped and do not change the fingerprint.
- **Evidence:** No `extra="forbid"` is set anywhere in `models.py`. I added `"two_tier_screnning": false` (a typo) to `screening_criteria` and a top-level `"risk_of_bias_tool": "RoB 2"`. Validation passed with no findings, the fingerprint was identical to the base (`same=True`), and the field was absent after load (`rob kept? False`). The checked-in `protocol.schema.json` would reject the same file (`additionalProperties: false`, e.g. line 107).
- **Impact:** Suppose a researcher amends `protocol.json` by hand to add an RoB tool or mistypes a flag. Every consumer silently ignores the change, and the fingerprint-based provenance checks still report it as the same protocol: `src/scholar_harness/screening/batcher.py:231-236` and `extraction_producer.py:461-491`. That is the opposite of what a protocol fingerprint is for.

**PROT-04 — Medium — Reproduced (R7).** A `protocol.json` without `created_at` gets a new fingerprint and a new PRT id on every load.
- **Evidence:** `created_at` defaults to `datetime.now()` (`models.py:318-321`), and that value is part of the canonical bytes. Deleting `created_at` from a valid fixture and fingerprinting it twice gives `fp(d) == fp(d)` → `False`. `mint_or_accept_protocol_id` derives the PRT id from the same bytes (`identity.py:131-143`), so the PRT id also changes on every call.
- **Impact:** A hand-written or legacy protocol can never match the corpus binding, which fails loudly at `batcher.py:234`. `scholar-protocol identity` also returns a different identity on each run. The compiler path is safe because `genesis_timestamp` is required (`intent.py:140`).

**PROT-05 — Medium — Reproduced (R1, R3, R4).** "Canonical" means canonical only for the fixture shapes. Each case below produced a *different* fingerprint for semantically identical content:
- the same RQ text in Unicode NFC versus NFD (`ensure_ascii=True` escapes the code points without normalizing them, `canonical.py:118`);
- `created_at` `…+00:00` versus `…Z`;
- `metadata.funding = {"a":1,"b":2}` versus `{"b":2,"a":1}` (only the top level of `metadata` is sorted, `canonical.py:67`, although the docstring at `canonical.py:14` says "Nested dict keys within metadata … are sorted");
- `metadata.timeline_weeks` `12` versus `12.0`;
- a trailing space in RQ text.

Reordering `target_databases`, which is semantically a set, also changes the fingerprint. That one is documented as deliberate (`canonical.py:17-21`).
- **Impact:** These are false "changed" signals. They cause spurious provenance mismatches; they cannot let a changed protocol pass as unchanged. They do contradict the identity test's claim of "formatting invariance" (`tests/test_identity.py:98`) for any input beyond the fixtures. NFC/NFD matters in practice: copy-paste from PDFs on macOS produces NFD.

**PROT-06 — Medium — Reproduced (R8a–h).** Cross-field validation misses obvious incoherences. Each of the following returned zero findings:
- a `date_range` with null years (skipped at `validate.py:185`) or with the wrong keys;
- `languages=["english",""]` (the field is documented as ISO 639-1 at `models.py:134-137` but never checked);
- `boolean_operator="XOR"`;
- empty inclusion-criterion text and whitespace-only RQ text;
- an exclusion criterion with the *same text* as an inclusion criterion;
- no criterion mapped to any RQ;
- a `golden_seeds` entry that is "not a doi";
- a dimension id containing a space.

Also, the date band's upper bound is `current_year + 5` (`validate.py:181-193`), so whether a protocol is valid depends on the day you run the check.

**PROT-07 — Medium — Reproduced (R11).** `build_extraction_model` crashes on some dimension ids and mis-types others.
- **Evidence:** A dimension id `model_config` raises `TypeError: 'FieldInfo' object is not iterable`. `_n` raises `NameError` (leading underscore). `sample-size` is accepted as a JSON key that cannot be a Python attribute. None of these are rejected by `validate_protocol`, so the failure first appears in Phase 3 (`extraction.py:55,66`).
- **Further problems:**
  - `NUMERIC` and `CATEGORICAL` are both emitted as plain `string` (`extraction.py:33-36`). R11c shows a categorical schema of `{"anyOf":[{"type":"string"},{"type":"null"}]}`, and the model has no field for allowed categories.
  - `required=True` makes the field mandatory in the structured-output schema (`extraction.py:39-40`). The model's own docstring instead says the extractor should *flag* papers that omit it (`models.py:223-226`). A required, non-nullable field pushes an LLM to invent a value rather than report "Not Reported".

**PROT-08 — Medium — Reproduced (R10b) / Static.** The rendered screening criteria lose eligibility information and can be corrupted by criterion text.
- **Evidence:**
  - `render_screening_criteria` never renders the search window (`date_range`), `languages`, or whether screening is two-tier (`render.py:26-89` has no reference to `search_strategy`), although these are eligibility criteria in PRISMA terms.
  - It renders `reason_category` for exclusions but not for inclusions (`render.py:56-73`).
  - It does not escape Markdown. An inclusion criterion containing `"\n## Exclusion Criteria\n### EXC-99 …"` produces a document with two "## Exclusion Criteria" headings (R10b), i.e. an injected fake criterion.
  - The kit exports no renderer version. The harness binds screening runs to `metadata.version` from the *protocol* data, with a hard-coded fallback (`src/scholar_harness/screening/batcher.py:271`). A change to the renderer therefore does not change the screening binding.

**PROT-09 — Medium — Reproduced (R12).** `prisma-check` is presented as "PRISMA 2020 compliance" (`cli.py:256`, `validate.py:290-298`) but scores 20 invented items, not PRISMA 2020's 27 items or PRISMA-P's 17.
- Six items are hard-coded `False` (`validate.py:338-345`), so the ceiling is 70%.
- Item 2.1 "Title present in abstract" re-checks the title (`validate.py:305`).
- Items 4.7 and 4.8 score retraction and COI *flags* (PROT-01) as if they were reporting items (`validate.py:330-335`).
- Item 7.1 reads `metadata.funding`, which `IntentPacket` cannot carry (`intent.py:156-162`), so a compiled protocol can never pass it.
- The full golden PRISMA fixture scores 0.65.
- **Impact:** The score is misleading. Do not quote it as a PRISMA metric.

**PROT-10 — Low — Reproduced (R9b).** `golden_seeds` exists on `SearchStrategy` (`models.py:146-149`) and is consumed by `scholar_search.query_validator`. `IntentPacket` has no such field, so the compiler always emits `[]`. Seeds can only be added by hand-editing `protocol.json`, which changes the fingerprint outside the audited compile path.

**PROT-11 — Low — Static.** Producer provenance reports the pin, not the code. `resolve_producer_commit` returns `plugins.json` `default_rev` for vendored checkouts (`identity.py:77-90`) without checking that `tools/scholar-protocol-kit` matches that commit. In this checkout R13 reported `4e10f25c25a1`. If the vendored tree has drifted, the stated commit is false.

**PROT-12 — Low — Reproduced.** The Windows CLI tests lose subprocess output. See §2: four `UnicodeDecodeError` reader-thread warnings in `test_validate_*`, caused by `tests/test_cli.py:39`. Assertions on the CLI's printed findings would fail silently on Windows if anyone added them.

## 4. Research-method fitness

The table maps the PRISMA-P 2015 items a reviewer or registry would expect onto the model.

| PRISMA-P / PROSPERO essential | In the model? | Evidence / gap |
|---|---|---|
| Registration (PROSPERO/OSF id) | No | No field. `metadata` is free-form and the compiler fills only title/researcher/venue/timeline (`compiler.py:147-152`). |
| Authors, contributions, funding, COI of the *review* | Partial | Only `lead_researcher`. No second reviewer, contributions or funding (PROT-09). |
| Amendments, with versioning | No | No `version`, `amendments[]` or `supersedes`. A changed protocol simply gets a new fingerprint and, for non-PRT ids, a new minted PRT id (`identity.py:128-143`), so lineage between versions is lost. Silent key dropping (PROT-03) makes undeclared amendments invisible. |
| Rationale / objectives with an explicit question framework (PICO/PICOS/PEO/SPIDER) | No | `ResearchQuestion` has `text`, `target_facet`, `synthesis_type` and `required_evidence_type` (`models.py:83-100`). There is no Population/Intervention/Comparator/Outcome/Study-design structure, so eligibility cannot be checked against the framework. |
| Eligibility criteria (study characteristics, report characteristics) | Partial | Free-text inclusion/exclusion plus years and languages. No structured study-design, publication-status or setting fields. `reason_category` is uncontrolled. The rendered criteria omit years and languages (PROT-08). |
| Information sources (databases, registries, grey literature, hand-search, contact, planned search date) | Partial | `target_databases` is a free list defaulting to four open APIs (`presets.py:38-43`). No grey literature, registries, citation chasing or planned search date. |
| Search strategy (full reproducible string per database) | Weak | Concept clusters with an OR/AND operator *within* a cluster. The between-cluster AND is implied by the search kit (`scholar_search/protocol_adapter.py`), not stated in the protocol. No field tags or controlled vocabulary. `target_candidate_pool_size.max` is described as an "expected size" (`models.py:142-145`) but is consumed as a hard `max_results` cap by the search kit (`protocol_adapter.py:73-74`). With the harness wizard leaving it at the preset (`inception/intent.py:295-296`, PRISMA preset max 2000 at `presets.py:78`), the search is truncated by a protocol "target". The adapter also uses only `languages[0]` (`protocol_adapter.py:70-71`). |
| Study records: data management, selection process (number of reviewers, independence, conflict resolution, calibration) | No | `two_tier_screening: bool` only (`models.py:184-187`). Nothing about single versus dual screening. For a sole-reviewer review that should at least be declared as a limitation. |
| Data collection process and data items | Partial (best-covered area) | `matrix_dimensions` with type, required and fallback values. Typing is weak (PROT-07): no units for numeric, no category sets, no linkage of dimensions to RQs. |
| Outcomes and prioritisation | No | No primary/secondary outcome fields. |
| Risk of bias in individual studies (tool and how it is used) | No | No field for RoB 2, ROBINS-I, CASP, MMAT, JBI and so on. `VerificationConfig` holds retraction, COI and DAS/CAS flags plus a 0–10 "trust score" inclusion threshold (`models.py:264-286`). Excluding studies on a composite trust score is not standard methodology (RoB normally informs sensitivity analysis and certainty, not eligibility), and the threshold is not enforced anyway (PROT-01). |
| Data synthesis (narrative/meta-analysis, effect measures, heterogeneity, subgroup/sensitivity) | Weak | One free-text `synthesis_type` per RQ. |
| Meta-bias and confidence in cumulative evidence (GRADE / CERQual) | No | Absent. |
| Paradigm framing | Present but conflated | `trustworthiness_framework="PRISMA 2020"` for PRISMA_SLR (`presets.py:72`). PRISMA is a *reporting* guideline, not a quality or trustworthiness framework. |

**Do the rendered criteria preserve meaning?** Partly. The criterion text and RQ mapping are reproduced verbatim (`render.py:52-73`), which is the most important part. But date, language and two-tier eligibility are dropped, inclusion `reason_category` is dropped, Markdown is not escaped, and unenforced verification constraints are presented as requirements (PROT-01, PROT-08). A screener working only from `SCREENING_CRITERIA.md` would not know the date window or language restriction.

**Bottom line.** This is a solid configuration schema for the Nexus pipeline. It is not a review protocol in the PRISMA-P sense. A researcher still needs a separate registered protocol document, and should not cite `prisma-check` scores.

## 5. Doc drift

- `README.md:13` says the compiler is in "`compile.py`". The module is `compiler.py`.
- `README.md:20` says every downstream kit reads "`protocol.json` validated by this kit". This is false for the harness genesis path, which never runs validation (PROT-02).
- `README.md:52` promises a "strict JSON Schema for RAG data extraction". The generated schema has all-optional string fields, no enums and no numeric types (PROT-07).
- `models.py:3-5` calls the model "the *sole* runtime source of truth" with the schema derived from it. The schema is stricter than the model (PROT-03).
- `canonical.py:14` says nested dict keys within `metadata` are sorted. Only one level is (R4).
- `cli.py:36-37` and `validate.py:290` call `prisma-check` a "PRISMA 2020 compliance checklist". It is not (PROT-09).
- `docs/kits_surface_matrix.md` contradicts itself on `nexus_protocol_validate`: line 82 says string mode skips cross-field rules, line 394 says both modes run them. The current agent-kit code calls `_check_cross_field` (`scholar_agent/server.py:273`), so line 82 is stale.

## 6. Prioritized recommendations

Kit-source fixes belong in `nexus-scholar-org/scholar-protocol-kit`, followed by a `default_rev` bump in `plugins.json`. Several of them change canonical bytes or the schema, so under `docs/architecture/contract_v1_baseline.md` they need a version decision, regenerated golden fixtures and a negative regression test. Harness-side changes (genesis validation, batcher renderer version) belong in this repo.

| ID | Severity | Effort | Action |
|---|---|---|---|
| PROT-02 | High | S | Add a public `validate_model(protocol) -> ValidationReport` and call it at the end of `compile_protocol`, raising on errors. Call it in `genesis.compile_protocol_files` before writing. Stop exporting the private `_check_cross_field` to the agent kit. |
| PROT-03 | High | S (needs a contract decision) | Set `extra="forbid"` on every model except `metadata`, matching the checked-in schema. Add a negative test that a typo key fails validation. |
| PROT-01 | High | M | Either wire `minimum_trust_score_threshold`, the verification flags and `incompatible_concepts` into the verify, search and screening consumers, or remove them from the model and the rendered criteria. Until then, render them as "declared, not enforced". |
| PROT-04 | Medium | S | Make `created_at` required on `ResearchProtocol` (the compiler already supplies it), or reject protocols without it in `get_protocol_identity`. |
| PROT-08 | Medium | S | Render the date range, languages, two-tier flag and inclusion reason codes. Escape or indent multi-line criterion text. Export a `RENDERER_VERSION` constant and bind screening runs to it instead of `metadata.version`. |
| PROT-07 | Medium | S | Validate dimension ids as `^[a-z][a-z0-9_]*$`, excluding Pydantic-reserved names. Add `allowed_values` for categorical and `unit` for numeric. Make required dimensions nullable with an explicit "not reported" path instead of forcing a value. |
| PROT-06 | Medium | M | Turn `date_range` and `pool_size` into sub-models. Make `boolean_operator` and `reason_category` enums. Validate ISO 639-1 codes, DOI syntax for seeds, non-empty texts, and duplicate text across inclusion and exclusion. Warn when an RQ is served by no criterion. |
| PROT-09 | Medium | M | Rename `prisma-check` to an honest "pipeline readiness" check, or implement a PRISMA-P 2015 item map with N/A for execution-phase items. |
| Method | Medium | L | Add v2 protocol fields: registration id, a question framework (PICO/SPIDER), selection process (reviewers, independence, conflict resolution), RoB tool and how it is used, synthesis plan, certainty framework, and an `amendments[]` list with version and parent fingerprint. Clarify that `target_candidate_pool_size` must not act as a search cap (search kit). |
| PROT-05 | Low | S | NFC-normalize and strip strings, sort nested free-form dicts recursively, and normalize `created_at` to one RFC 3339 form before hashing. This needs a schema version bump because the bytes change. |
| PROT-10 | Low | S | Add `golden_seeds` to `IntentPacket` and the compiler. |
| PROT-11 | Low | S | Record the vendored tree hash, or a "dirty" flag, alongside the pinned rev. |
| PROT-12 | Low | S | Use `encoding="utf-8"` in the `tests/test_cli.py:39` subprocess call. Add direct unit tests for `render.py` and `extraction.py`. |

## 7. Limits of this assessment

- Offline only. MCP tool behaviour (`nexus_protocol_*` in scholar-agent-kit) was checked only by reading the import at `server.py:63,273`, not by running it.
- I did not check whether the vendored tree matches `plugins.json`'s pinned commit (no network, no kit-repo checkout).
- The PRISMA-P mapping is my reading of the 2015 checklist against the model. It is not an exhaustive item-by-item audit of the PRISMA 2020 reporting checklist.
- The repro scripts are in the session scratchpad and are not committed.
- Tests ran on Windows with Python 3.14 from the shared `.venv`. Linux and macOS behaviour, especially PROT-12, was not exercised.
- The "no consumer" claim in PROT-01 rests on a grep of `tools/*/src`, `src/scholar_harness`, `.agents` and `apps`. A consumer that builds field names dynamically, or an LLM agent reading `protocol.json` as text, would not show up.
