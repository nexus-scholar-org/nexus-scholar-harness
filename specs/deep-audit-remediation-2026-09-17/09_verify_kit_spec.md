# Scholar Verify Kit Remediation Specification

**Status:** Proposed / implementation-ready  
**Owner:** scholar-verify-kit maintainers  
**Date:** 2026-09-17  
**Scope:** verification APIs, CLI, schemas, Phase-4 artifacts, and agent adapters

## 1. Architecture and confirmed findings

The kit implements retraction, open-science, COI, risk-of-bias, trust-context, and verbatim-claim streams, exposed through a Typer CLI (`tools/scholar-verify-kit/src/scholar_verify/cli.py:1-24`). Workspace validation accepts either `protocol.json` or `INDEX.md` (`cli.py:27-31`). Core Phase-4 output is JSON plus Markdown under `phase4/` (`cli.py:43-48`), and `all` runs four streams sequentially (`cli.py:197-222`).

Confirmed remediation drivers:

1. **P0 runtime failure:** `verbatim_claims_cmd` calls `re.search` (`cli.py:242-253`) but `re` is absent from imports (`cli.py:13-22`).
2. **Input-schema drift:** standalone CLI requires a bare JSON list (`cli.py:238-240`), while the MCP adapter accepts both a list and `{claims:[...]}` (`tools/scholar-agent-kit/src/scholar_agent/server.py:932-940`).
3. **Output-schema drift:** CLI writes `{metrics, results}` (`cli.py:260-266`), while MCP documents/returns status, metrics, failure reasons, and claims (`server.py:899-905`).
4. **Non-atomic output:** `_write` writes JSON and Markdown independently (`cli.py:43-48`); stream-local writers repeat this pattern (`tools/scholar-verify-kit/src/scholar_verify/coi.py:300-304`, `risk_of_bias.py:262-266`, `retraction.py:282-287`).
5. **Weak workspace gate:** an `INDEX.md` alone qualifies as a workspace (`cli.py:27-31`), without protocol fingerprint or layout validation.
6. **Partial `all` commits:** earlier streams remain written when a later stream fails (`cli.py:197-222`), with no run-level outcome manifest.
7. **Overwrite policy is inconsistent:** `_confirm_overwrite` checks only the JSON target (`cli.py:63-66`), while some commands expose custom outputs and verbatim output writes without the common writer (`cli.py:225-267`).
8. **Dependency declaration is broader than code evidence warrants:** runtime declares `requests` (`tools/scholar-verify-kit/pyproject.toml:13-17`); dependency audit and lock verification are required before removal or replacement.
9. **Retraction-only evidence can be suppressed.** Trust-context considers a study present only when RoB or COI data exists (`tools/scholar-verify-kit/src/scholar_verify/trust_context.py:153-156`) and checks flags only for present studies (`:158-167`). A reproduced retraction-only flagged study yielded `UNVERIFIED` with zero flagged aggregate despite its detail showing the flag, violating the documented any-flag blocking rule (`:10-19,129-141`).
10. **Open-science negation collides with positive matching.** Generic positive `data\s+availab` patterns (`open_science.py:19-32`) match “No data available,” while negation is honored only when no positive matched (`:104-118`). The phrase was reproduced as `statement-only` rather than explicitly unavailable.
11. **Repository links are not associated locally or by type.** Every whitelisted URL in a document can be associated with both DAS and CAS (`open_science.py:93-100,122-138`). An unrelated repository URL can inflate a positive statement to `public+link` and thereby affect STRONG trust.
12. **`--dry-run` is not network-free.** Retraction dry-run performs the live OpenAlex/Crossref calls and sleeps, then merely suppresses file output (`cli.py:86-97`), contrary to the documented plumbing-only behavior.
13. **CLI and MCP `all` differ.** CLI runs the four core streams (`cli.py:196-222`); MCP also attempts trust-context, while MCP defaults `skip_retraction=True` and can return success with no written artifact for an explicit retraction request (`tools/scholar-agent-kit/src/scholar_agent/server.py:1005-1119`).
14. **Correction severity is internally inconsistent.** Crossref corrections/addenda are flagged (`retraction.py:22-28,160-167`) and any flag blocks trust (`trust_context.py:129-140`), while the report labels corrections low severity and non-invalidating (`retraction.py:236-245,271-276`). `_FLAG_REASON_SENSITIVE` exists but is unused (`trust_context.py:40`).
15. **Phase-4 writes bypass the harness audit/state convention.** Direct CLI/MCP runs create significant artifacts but do not append `audit/journal.jsonl` or synchronize `project.json`/`INDEX.md`.
16. **Documentation paths and coverage drift.** README names `literature/screening/included.json`, while implementation and canonical harness use `literature/included.json`; trust-context and verbatim commands are omitted.

## 2. Goals and non-goals

### Goals

- Make every verification result reproducible, schema-versioned, provenance-rich, and scientifically bounded.
- Unify API, CLI, and MCP inputs/outputs.
- Prevent partial or stale Phase-4 publication.
- Preserve item-level uncertainty and distinguish absence of evidence from evidence of absence.

### Non-goals

- Claim that automated checks replace human risk-of-bias, COI, or retraction assessment.
- Infer undeclared COI or unavailable data from missing text.
- Treat lexical/verbatim matching as semantic entailment.
- Expand domain-specific risk-of-bias rules without a separately reviewed methodology change.

## 3. Normative requirements

- **VR-001 MUST** import every runtime symbol; the verbatim command MUST execute in a clean environment.
- **VR-002 MUST** expose one canonical claims-ledger schema through API, CLI, and MCP.
- **VR-003 MUST** version every input and output artifact and validate before computation.
- **VR-004 MUST** require a valid workspace, protocol fingerprint, corpus fingerprint, and manifest fingerprint for Phase-4 runs.
- **VR-005 MUST** reject stale or mixed-run inputs rather than combining them.
- **VR-006 MUST** use canonical IDs and vocabulary from `10_cross_kit_contracts.md`.
- **VR-007 MUST** represent `CLEAR`, `FLAGGED`, `UNRESOLVED`, `NOT_APPLICABLE`, and `NOT_CHECKED` as distinct trust states per the shared axis in `10_cross_kit_contracts.md` (XC-041).
- **VR-008 MUST NOT** convert an API/network failure into `CLEAR`, `NOT_RETRACTED`, or an equivalent reassuring label.
- **VR-009 MUST** retain source, checked timestamp, query identifier, response status, and evidence locator for each external verification.
- **VR-010 MUST** distinguish verbatim support from entailment and keep them on the shared orthogonal axes of `10_cross_kit_contracts.md` (XC-041): retrieval (`SOURCE_AVAILABLE|SOURCE_UNAVAILABLE`), lexical support (`SUPPORTED_VERBATIM|PARTIAL_MATCH|NOT_FOUND|NOT_CHECKED`), entailment (`ENTAILED|CONTRADICTED|UNCERTAIN|NOT_ASSESSED`), and trust (`CLEAR|FLAGGED|UNRESOLVED|NOT_APPLICABLE|NOT_CHECKED`). `SOURCE_UNAVAILABLE` belongs to the retrieval axis, not the lexical axis; it MUST NOT be emitted as a lexical-support value. Verbatim output MUST NOT emit `VERIFIED` as a synonym for scientific truth.
- **VR-011 MUST** retain each per-claim verdict; aggregates alone are insufficient.
- **VR-012 MUST** validate thresholds to `0 <= threshold <= 1` and record normalization/tokenization versions.
- **VR-013 MUST** scope RQ attribution by canonical `claim_id`, not mutable `(study_id, claim_text)` equality.
- **VR-014 MUST** write JSON, Markdown, and run manifest transactionally; `all` MUST either commit the complete requested set or publish an explicit `PARTIAL` run manifest without replacing the last complete set.
- **VR-015 MUST** use atomic temp-write, fsync where supported, and replace semantics.
- **VR-016 MUST** close network resources on success, failure, and cancellation and SHOULD use bounded concurrency with provider-specific limits.
- **VR-017 MUST** emit the shared structured outcome and append one audit event after artifact commit.
- **VR-018 MUST** include deterministic configuration and rule-set versions in risk-of-bias output.
- **VR-019 MUST** label automated RoB as a reproducible decision aid, not a substitute for full-text human appraisal.
- **VR-020 MUST** preserve verbatim quotations and locators behind each COI/open-science classification and MUST distinguish `NO_STATEMENT_FOUND` from `NO_CONFLICT_DECLARED`.
- **VR-021 SHOULD** support offline fixtures/cache replay while marking cache age and origin.
- **VR-022 SHOULD** support `--dry-run`, `--force`, `--json`, and `--fail-on <state>` consistently across commands.
- **VR-023 MUST** treat a study as covered when any applicable Phase-4 stream has evidence. A retraction/expression-of-concern flag MUST remain visible and apply the approved blocking policy even if RoB or COI data is absent.
- **VR-024 MUST** evaluate explicit unavailability/negation before generic positive availability patterns and retain the matched local text span.
- **VR-025 MUST** associate data/code links by signal type and documented proximity/context. An unrelated URL elsewhere in a document MUST NOT upgrade DAS or CAS.
- **VR-026 MUST** define `--dry-run` unambiguously. If documented as plumbing validation, it MUST perform zero network calls and writes; a no-write live run requires a differently named option.
- **VR-027 MUST** use one public stream orchestrator for CLI and MCP. `all`, skip flags, defaults, statuses, and written artifacts MUST have identical semantics.
- **VR-028 MUST** implement an approved publication-event severity policy. Retraction and expression-of-concern, correction, and addendum states MUST not collapse to one undifferentiated blocking flag unless the approved policy explicitly chooses that behavior.
- **VR-029 MUST** integrate significant Phase-4 artifact commits with canonical workspace audit/state synchronization, either through the harness wrapper or an injected audit service.

## 4. Canonical behavior

Public Python APIs SHALL accept validated models and return typed result models without writing. A separate artifact service SHALL serialize and commit results. CLI commands SHALL be thin wrappers over those APIs.

The canonical claims input is an object containing `schema_version`, `artifact_type="claims_ledger"`, fingerprints, and `claims`. Bare arrays are legacy v0 only. Each claim includes stable `claim_id`, `claim_text`, `claim_kind`, `study_ids`, citation/evidence locators, and generation provenance.

Each Phase-4 stream emits a common header plus stream-specific `items` and `summary`. Summary counts MUST be derivable from items and validated before commit. Markdown is a rendering of JSON, never an independent source of truth.

CLI exit codes: 0 complete success; 2 validation/usage; 3 scientific attention threshold reached via `--fail-on`; 4 partial/unresolved dependency; 5 internal failure. Human text goes to stderr or a presentation channel; `--json` prints only the outcome envelope.

## 5. Migration and compatibility

1. Add v1 readers for legacy bare claims lists and legacy Phase-4 files; adapters MUST emit migration warnings.
2. Write only current schemas. Never rewrite legacy inputs in place.
3. Preserve existing command names and default artifact basenames for one major line.
4. Add `--force` as the explicit noninteractive overwrite contract; interactive prompts remain only on TTY.
5. Agent MCP and CLI switch to the same API and fixtures in the same release.

## 6. Prioritized tasks

### P0

1. Add the missing `re` import and an end-to-end verbatim CLI test.
2. Define canonical claims and outcome models; unify CLI/MCP behavior.
3. Add fingerprint gates and transactional Phase-4 run commits.
4. Correct uncertainty vocabulary and prohibit failure-to-clear conversion.
5. Fix trust coverage so retraction-only evidence blocks as configured.
6. Correct open-science negation precedence and typed/proximal link association.

### P1

1. Split pure computation from persistence; consolidate duplicate save helpers.
2. Add item-level provenance, evidence locators, rule-set versions, and run manifests.
3. Normalize overwrite, dry-run, JSON, and exit-code behavior.
4. Add lifecycle-safe clients, bounded concurrency, cache provenance, and cancellation tests.
5. Unify CLI/MCP stream orchestration, true dry-run semantics, publication-event severity, and harness audit/state integration.

### P2

1. Externalize reviewed RoB profiles without weakening deterministic defaults.
2. Add schema-generated documentation and migration tooling.
3. Add calibration corpora and report sensitivity/specificity for lexical classifiers where defensible.

## 7. Failure-focused test matrix

| Failure/edge case | Required assertion |
|---|---|
| Invoke `verbatim-claims` | no `NameError`; canonical output |
| Bare list legacy input | migrated with warning and stable IDs |
| Dict claims input through CLI and MCP | identical item verdicts and summary |
| Threshold -0.1 or 1.1 | validation error, no output |
| Missing extracted source | `SOURCE_UNAVAILABLE`, never false/clear |
| Provider timeout/429/invalid JSON | `UNRESOLVED` with source diagnostics |
| Protocol or corpus fingerprint mismatch | hard rejection, no Phase-4 commit |
| JSON commit succeeds, Markdown write fails | neither promoted; previous set intact |
| Third stream fails in `all` | explicit partial run staged; complete alias unchanged |
| Cancellation during network batch | clients closed; resumable manifest |
| Empty corpus | valid zero-count artifacts, no divide-by-zero |
| Duplicate/missing IDs | schema error with item locations |
| Same fixture through API/CLI/MCP | canonical JSON equivalent |
| Summary manually disagrees with items | validation rejects commit |
| No COI section | `NO_STATEMENT_FOUND`, not `NO_CONFLICT_DECLARED` |
| Retraction-only flagged study with no RoB/COI | covered and `BLOCKED` under blocking policy; flag retained |
| `No data available.` | explicitly unavailable with matched span |
| Positive data statement plus unrelated code URL | data/code labels associated independently; no false `public+link` |
| Dry-run retraction | zero network calls and zero writes |
| CLI versus MCP `all` | identical stream selection, skip semantics, statuses, and artifact set |
| Correction versus retraction | approved distinct severity and trust behavior |
| Direct Phase-4 artifact commit | one canonical audit event and refreshed workspace state |

## 8. Definition of done

- VR-001 through VR-020 have automated coverage.
- Full verify-kit and harness MCP suites pass on supported OS/Python combinations.
- Clean wheel install, import, and every command `--help` pass.
- Golden schemas and fixtures prove API/CLI/MCP parity.
- No Phase-4 command can publish a mixed, stale, or partially overwritten artifact set.
- Retraction-only evidence cannot disappear behind missing RoB/COI coverage.
- Open-science negation and unrelated links cannot inflate availability/trust.
- CLI and MCP select and report identical verification streams.
- Methodological documentation states the limits of every automated stream.
- Canonical kit repo, vendored snapshot, and manifest pin are synchronized.

## 9. Dependencies, risks, and documentation

Depends on canonical contracts in `10_cross_kit_contracts.md`, protocol fingerprint APIs, and harness audit logging. Risks include relabeling historical states, apparent metric changes after uncertainty correction, and migration ambiguity for ID-less claims. Preserve original payload hashes and emit explicit migration provenance.

Update `README.md`, CLI reference, Python API reference, Phase-4 schema reference, methods/limitations notes, `docs/kits_surface_matrix.md`, MCP documentation, and workspace artifact documentation. Include complete examples for success, partial provider failure, stale fingerprints, and legacy migration.
