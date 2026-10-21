# Packet T-D0D2 — Screening decision contract reader + validator (harness)

**Status:** dispatched. **Date:** 2026-10-20.
**Origin:** `docs/architecture/packets_from_uav_demo_2026-10-19.md` (draft packets D-2 and
the promotion of the demo's validator), ratified by the orchestrator review of
2026-10-19/20. **Delivery lane:** `RELEASE` (see rationale below).

> **Lane rationale.** The diff adds a public CLI surface (`agent_screen.py validate`) and
> sits adjacent to the screening-decision path. Per
> `docs/architecture/test_gate_policy.md` ("Escalate to `RELEASE` immediately when its
> actual diff changes … a public API/CLI/MCP contract"), the lane is `RELEASE`, not
> `STANDARD`, even though no Contract v1 semantics change.

---

## TASK_ID

`T-D0D2` (harness path mapping in `docs/architecture/test_gate_manifest.json` → `T-130`).

## OBJECTIVE

Promote the UAV demo's screening-decision schema reader and validator from a
workspace-local driver into a reusable, domain-parameterized **harness** module, and
expose it as a first-class, re-runnable command.

The module must, for any set of screening decision files:

1. read each row's canonical fields, falling back to an **explicit, tagged alias map**;
2. classify each file into exactly one of `VALID` / `DEBT` / `BAD`;
3. record every debt tag explicitly and **never fabricate** an absent value;
4. emit a **debt ledger** (per-file, per-tag counts) consumable by reports;
5. never mutate a producer file.

## OWNER_SURFACE

**Harness — this repository.** No `scholar-*-kit` is touched. See
`TOOLKIT_SYNC_AND_PIN_PLAN`.

---

## DEPENDENCIES_AND_EVIDENCE

| Dependency | Evidence | Status |
|---|---|---|
| Demo reference implementation | `workspaces/uav-crop-weed-v03/_drivers/v03_scr1_schema.py` (237 lines) | present, read-only reference |
| Demo ledger artifact | `workspaces/uav-crop-weed-v03/calibration_v03/v03_scr1_schema_debt_report.json` | present, read-only reference |
| Frozen instrument (field authority) | `workspaces/uav-crop-weed-v03/_drivers/v03_scr1_pass1_prompt_template.txt` | present, read-only reference |
| Harness screening package | `src/scholar_harness/screening/{batcher,collector,integrity,report,worker}.py` | present |
| Harness audit writer | `src/scholar_harness/workspace/audit.py` → `log_event(workspace, action, description, *, agent, inputs, outputs, parameters, metrics, status, refresh_index)` | present |
| CLI surface | `src/scholar_harness/agent_screen.py` (subparsers `prepare|status|collect|rec|rev|app|cal|ceval|def`) | present |
| Baseline drift | `generate_contract_baseline.py --check` → `Contract baseline current`; `generate_contract_schemas.py --check` → clean; `generate_two_study_contract_fixture.py --check` → clean; `generate_nexus_scholar_pins.py --check` → `[OK] … in sync` | **all four green at `c10d281`** |
| Harness suite | `uv run pytest -q` → green at `c10d281` (no failures; deprecation warnings only) | green |
| Known baseline failure | `tools/scholar-search-kit/tests/test_enrichment.py::test_hydrate_from_openalex_success` and `::test_hydrate_missing_abstracts_fallback_to_openalex` **FAIL** against the pre-existing dirty `tools/scholar-search-kit/` tree | pre-existing, **out of scope**, do not fix, do not absorb |

**Base commit:** `c10d2819e92556cabd8124e918a1bb672504c9ec`.

---

## GOVERNING_REQUIREMENTS

### G1 — The frozen instrument is the only source of required fields

Derive the required-field set from the frozen instrument, **never** from what the last
agents happened to write. Extras are allowed and never required. Over-constraining
invents defects. *(Demo lesson 28.)*

### G2 — Three tiers, with debt as a first-class outcome

| Tier | Meaning |
|---|---|
| `BAD` | structurally unusable: unparseable, parent unattested/missing, wrong row count, id/order mismatch vs parent view, missing id, decision outside the vocabulary, non-canonical filename, BOM, unsupported schema major version |
| `DEBT` | decision-complete and usable, but a canonical field is absent, alias-named, non-numeric, out of range, or the rationale sits only under `reason` |
| `VALID` | every canonical field present and well-formed, and no debt tags |

A `DEBT` file is **not** a failure and **not** silently repaired. It is reported with
tags so triage can route it. *(Demo lessons 27, 30, 31.)*

### G3 — Never fabricate; never coerce silently

- Absent canonical field → value `None` + an explicit debt tag. Never a default, never a
  guess, never a synthesized criterion reference.
- A non-numeric confidence (`"high"`) → value `None` + `CONFIDENCE_NON_NUMERIC`. **No
  numeric value is invented.**
- An alias key is recognized **only** when it is in the configured alias map, and its use
  is **always tagged** (`ALIAS_REASON_CODE:<key>`).
- Unknown keys are preserved and reported as advisory `UNKNOWN_KEYS`, never dropped.

### G4 — The parent artifact is the count authority

Row counts and id order are verified against the **parent batch manifest and its
view**, never against a dispatch prompt or a producer self-report. *(Demo lessons 33, 41.)*

### G5 — Filename canonicity is part of the contract

A decision file whose name does not match the canonical pattern must be **surfaced** as
`FILENAME_NOT_CANONICAL`, not silently invisible. A coarse inventory that globs and
`int()`-parses names silently matches malformed names and reports a clean count.
*(Demo lesson 29.)*

### G6 — Strict UTF-8, no BOM; detect BOM explicitly

Read decision files as strict UTF-8. A leading `EF BB BF` must produce the explicit
finding `BOM_DETECTED`, not a generic parse error. Never write a BOM'd file. *(Demo
lesson 39.)*

### G7 — Domain configuration lives outside the code

The canonical field set, allowed extras, alias map, decision vocabulary, expected
instrument SHA prefixes, embedded reason-code pattern, and file-name patterns are
**configuration**, supplied per workspace. The module's defaults must be
**domain-free**: no UAV tokens, no hardcoded instrument SHAs, no domain reason-code
prefixes. *(Demo lesson 21; HCM-1 promotion rule.)*

### G8 — No producer mutation; new file only

The reader never rewrites, repairs, renames, or deletes a decision file. It writes only
**new** sidecar output. *(Demo lessons 25, 30.)*

### G9 — Fail closed, publish nothing on failure

The reader is a **classification and reporting** surface. It does not publish a
Contract v1 artifact, does not write `included.json`/`excluded.json`, and does not
mutate the registry. A `BAD` file blocks collection from that source.

### G10 — Do not weaken the Contract v1 collector

**The new reader must NOT be wired into the Contract v1 dual-screening publication path.**
The Contract v1 collector (`src/scholar_harness/screening/collector.py`) requires
`decision_id`, `screener_id`, `method`, `decided_at`, `reason`, `parent_decision_ids` —
a **different schema** from the agent-lane schema this reader targets. Its existing
fail-closed provenance requirements, `ScreeningIntegrityRefused` codes, and refusal
messages remain byte-for-byte unchanged. *(AG plan: "Preserve existing Contract v1
decision meanings.")*

### G11 — Deterministic, idempotent, append-only output

The same inputs produce byte-identical report content. The command must **refuse** to
overwrite an existing report (`REPORT_EXISTS`) rather than silently rewriting it.
*(Compass §3 "Determinism"; demo lesson 25.)*

### G12 — Audit every workspace mutation

The report sidecar is a workspace mutation and **must** be recorded in
`audit/journal.jsonl` through `scholar_harness.workspace.audit.log_event` — never by
hand-appending to the journal. The event must carry the real actor, the real inputs and
outputs, and a truthful status. `log_event` also refreshes `INDEX.md`; keep that
behavior.

---

## ALLOWED_PATHS

```
src/scholar_harness/screening/decision_contract.py      (NEW)
src/scholar_harness/screening/__init__.py                (export only; no behavior change)
src/scholar_harness/agent_screen.py                      (add the `validate` subcommand only)
tests/test_screening_decision_contract.py                (NEW)
tests/fixtures/screening_decision_contract/**            (NEW)
```

## FORBIDDEN_PATHS

Everything else. Explicitly:

```
src/scholar_harness/contracts/**              frozen Contract v1 — no edits, no regeneration
src/scholar_harness/screening/{batcher,collector,integrity,report,worker}.py
src/scholar_harness/**                        (any other harness module)
tools/**                                      no toolkit change in this packet
workspaces/**                                 READ-ONLY reference only; write nothing
packaging/**  .agents/plugins/**               no pin or vendor change
apps/**                                       no UI change
docs/architecture/contract_v1_baseline*        contract-locked
docs/architecture/cross_kit_contract_v1.md     contract-locked
```

**Pre-existing dirty files you must not modify, stage, revert, or absorb** (baseline at
`c10d281`):

```
apps/research-ui/AGENTS.md
docs/README.md
tools/scholar-search-kit/src/scholar_search/{dedup,enrichment,models}.py
tools/scholar-search-kit/src/scholar_search/providers/{arxiv,openalex,pubmed,semanticscholar}.py
workspaces/uav-pilot-demo/**                  (staged, 19 files)
workspaces/uav-crop-weed-v03/**               (untracked)
docs/lessons/**                               (untracked)
docs/architecture/packets_from_uav_demo_2026-10-19.md   (untracked)
```

---

## INPUTS

Read-only reference material:

| Path | Use |
|---|---|
| `workspaces/uav-crop-weed-v03/_drivers/v03_scr1_schema.py` | Reference implementation. Promote its logic; do not copy its domain constants. |
| `workspaces/uav-crop-weed-v03/_drivers/v03_scr1_pass1_prompt_template.txt` | The frozen instrument: authoritative for the canonical field set (lines 43–45). |
| `workspaces/uav-crop-weed-v03/calibration_v03/v03_scr1_schema_debt_report.json` | Expected ledger shape; verify your ledger reproduces comparable per-tag counts. |
| `src/scholar_harness/screening/integrity.py` | House style for a pure, fail-closed harness module (no I/O side effects, typed refusal). |
| `src/scholar_harness/screening/batcher.py` | `_screening_dir`, `_load_decisions`, `_load_decision_payload` conventions. |
| `src/scholar_harness/workspace/audit.py` | `log_event` signature and guarantees. |
| `src/scholar_harness/agent_screen.py` | CLI shape and subparser conventions. |

**Workspace contract configuration** — the module must read its domain configuration from
a JSON file, e.g. `literature/screening/decision_contract.json`, with this shape
(all keys optional; missing = domain-free default):

```json
{
  "schema_version": "1",
  "canonical_fields": ["screening_id", "decision", "reason_code", "confidence", "one_line_support"],
  "allowed_extras": ["reason", "criterion_refs", "moderation_status", "moderation_redacted"],
  "reason_code_aliases": {"exclusion_reason_code": "reason_code"},
  "decision_vocabulary": ["INCLUDE", "EXCLUDE", "PENDING"],
  "expected_criteria_sha256_prefix": "",
  "expected_prompt_sha256_prefix": "",
  "embedded_reason_code_pattern": "",
  "decision_file_pattern": "batch_{n:04d}_decisions_{family}.json",
  "batch_file_pattern": "batch_{n:04d}.json",
  "view_file_pattern": "batch_{n:04d}.view.json"
}
```

---

## OUTPUTS

1. **`src/scholar_harness/screening/decision_contract.py`** — the module. Public surface:

   - a frozen, typed configuration object loaded from the contract JSON, with
     domain-free defaults;
   - `normalize_row(row, contract) -> (canonical_row, tags)`;
   - `classify_decision_file(path, contract, *, parent_batch=None, parent_view=None)
     -> FileClassification` where `FileClassification` carries `tier`, `structural`,
     `debt`, `advisory`, `header`, `rows`;
   - `build_debt_ledger(classifications) -> dict` (per-file, per-tag counts, deterministically
     ordered);
   - the tag vocabulary (debt prefixes, advisory prefixes, structural codes) exposed as
     module-level constants in **one** place.

2. **`agent_screen.py validate <workspace> [--out PATH] [--contract PATH]`** —
   - scans the workspace's screening decision directory,
   - writes a **new** JSON report (default
     `literature/screening/decision_contract_report.json`),
   - **refuses** to overwrite an existing report (`REPORT_EXISTS`),
   - prints a one-line summary (counts per tier),
   - logs one audit event via `log_event`.

3. **`tests/test_screening_decision_contract.py`** + fixtures under
   `tests/fixtures/screening_decision_contract/`.

---

## ACCEPTANCE_CRITERIA

| ID | Criterion |
|---|---|
| AC-1 | Module exists at `src/scholar_harness/screening/decision_contract.py`, imports cleanly, and contains **no** UAV/domain token: no `UAV`, `weed`, `crossref`, `openalex`, `9ae1f97d`, `0c7f129d`, no `INC-\d{2}`/`EXC-\d{2}` literal. A test asserts this. |
| AC-2 | Default configuration is domain-free: no expected SHA prefixes, no embedded reason-code pattern, no aliases. The module returns `DEBT`/`VALID` correctly with defaults — a contract with no configured prefixes does **not** make every file `BAD`. |
| AC-3 | Canonical rows produce `VALID` with zero debt and zero advisory tags. |
| AC-4 | One fixture per alias class (`exclusion_reason_code`, `pending_reason_code`, `inclusion_hint`, `reason_CODE`) → `DEBT` with tag `ALIAS_REASON_CODE:<key>`, and the canonical value copied **verbatim**. |
| AC-5 | Missing `confidence` → `DEBT` with `CONFIDENCE_ABSENT` and canonical value `None`. |
| AC-6 | Non-numeric confidence (`"high"`) → `DEBT` with `CONFIDENCE_NON_NUMERIC`, canonical value `None`, and **no numeric value anywhere in the output**. |
| AC-7 | Out-of-range confidence → `DEBT` with `CONFIDENCE_OUT_OF_RANGE`, value `None`. |
| AC-8 | Rationale present only under `reason` → `DEBT` with `RATIONALE_IN_REASON_ONLY`. |
| AC-9 | Absent reason code → `DEBT` with `REASON_CODE_ABSENT`. |
| AC-10 | Reason code recoverable only from text → `DEBT` with `REASON_CODE_EMBEDDED_IN_TEXT`, value extracted, extraction explicitly tagged. |
| AC-11 | Unknown keys → advisory `UNKNOWN_KEYS:<sorted keys>`; tier stays `VALID`/`DEBT`, never `BAD`. |
| AC-12 | File with no canonical and no alias-decodable field → `BAD`. |
| AC-13 | Unattested header (`screener_id` mismatch vs configured family, or missing/incorrect instrument SHA when one **is** configured) → `BAD`. |
| AC-14 | Row count != parent batch manifest `n_records` → `BAD` with `ROW_COUNT:<got>!=<expected>`. |
| AC-15 | Decision id order != parent view id order → `BAD` with `ID_ORDER_MISMATCH_VS_VIEW`. |
| AC-16 | Missing/empty `screening_id` on a row → `BAD`. |
| AC-17 | Decision outside the configured vocabulary → `BAD`. |
| AC-18 | Non-canonical decision filename (e.g. 6-digit padding) → surfaced as `FILENAME_NOT_CANONICAL`, **not** silently absent. |
| AC-19 | BOM-prefixed file → `BAD` with the explicit code `BOM_DETECTED`. |
| AC-20 | Malformed JSON → `BAD` with `JSON_PARSE:*`. |
| AC-21 | Missing parent (batch and view both absent) → `BAD` with `PARENT_MISSING`, not a silent pass. |
| AC-22 | Stale instrument: configured `expected_criteria_sha256_prefix` does not match the file's attested `criteria_sha256` → `BAD`. |
| AC-23 | Unsupported schema major version in the contract config → `BAD` with `SCHEMA_VERSION_UNSUPPORTED`. |
| AC-24 | The reader **never** writes to the decisions directory. A test snapshots the decisions tree (paths + bytes + mtimes) before and after a run and asserts byte equality. |
| AC-25 | The reader never publishes a Contract v1 artifact and never writes `included.json`/`excluded.json`/`prisma_screening_report.md`. Asserted by test. |
| AC-26 | Determinism: two runs over identical inputs produce byte-identical report content. Asserted by test. |
| AC-27 | Idempotency conflict: running `validate` twice against the same `--out` path refuses the second run with `REPORT_EXISTS` and leaves the first report byte-identical. Asserted by test. |
| AC-28 | The debt ledger reports per-file and per-tag counts and reconciles: `sum(files_by_tier) == files_scanned`, and the ledger's per-file tier counts match the per-file classifications. Asserted by test. |
| AC-29 | `agent_screen.py validate <workspace>` writes the report, prints a per-tier summary, and logs exactly one audit event through `log_event` with action `SCREENING_VALIDATION`, the report path in `outputs`, and the real actor. Asserted by test (monkeypatched `log_event`). |
| AC-30 | `agent_screen.py` **existing** subcommands (`prepare|status|collect|rec|rev|app|cal|ceval|def`) keep their current behavior and their current help text is unchanged for those subcommands. No existing harness test regresses. |
| AC-31 | The Contract v1 collector path is **untouched**: `git diff` shows no change to `collector.py`, `batcher.py`, `integrity.py`, `worker.py`, `report.py`, and no change to `src/scholar_harness/contracts/**`. Asserted by diff inspection at review. |
| AC-32 | `uv run pytest -q` is green, including the new test file, with **no** reduction in the count of previously passing tests. |
| AC-33 | The four baseline checks remain green: `generate_contract_baseline.py --check`, `generate_contract_schemas.py --check`, `generate_two_study_contract_fixture.py --check`, `generate_nexus_scholar_pins.py --check`. |
| AC-34 | `uv run ruff check scripts/` passes (CI scopes ruff to `scripts/`). |
| AC-35 | The module's public names are documented in the module docstring, including the explicit statement that it is **not** a Contract v1 publication surface and does not replace the collector's provenance gates. |

---

## NEGATIVE_CASES

Each must fail closed, and each must have a test:

1. **Missing parent** — decision file with no batch manifest and no view → `BAD`/`PARENT_MISSING`.
2. **Wrong workspace** — a decision file whose `screening_id` values belong to another
   workspace's corpus → `BAD`/`ID_ORDER_MISMATCH_VS_VIEW`.
3. **Stale fingerprint** — attested instrument SHA does not match the configured
   expected prefix → `BAD`.
4. **Unknown major version** — contract config declares schema major `2` while the
   reader supports major `1` → `BAD`/`SCHEMA_VERSION_UNSUPPORTED`.
5. **Invalid identifier** — row missing `screening_id`, or `screening_id` present but
   empty → `BAD`.
6. **Idempotency conflict** — second run against an existing report path →
   `REPORT_EXISTS`, first report byte-identical, no mutation.
7. **Fabrication attempt** — a row missing `confidence` must **not** produce `0.0`,
   `1.0`, or any numeric default; the output must contain `None` and the debt tag.
8. **Silent coercion attempt** — a row carrying only `exclusion_reason_code` must not
   yield an untagged `reason_code`; the alias use must be tagged.
9. **Coarse-inventory green** — a decision file with a 6-digit-padded filename must
   produce a visible `FILENAME_NOT_CANONICAL` finding, not a clean inventory count.
10. **Prompt-authority inversion** — a dispatch prompt claiming a row count that
    disagrees with the parent manifest → the manifest wins; the disagreement is a
    `BAD`/mismatch finding, never a silent acceptance of the prompt's figure.
11. **Producer mutation** — any attempt (in test) to observe writes into the decisions
    directory → must be empty.
12. **Vacuous-green guard** — a test asserts the validator *can* fail: a deliberately
    malformed fixture must produce a non-empty `structural` list. A validator that
    cannot fail proves nothing.

---

## VALIDATION_COMMANDS

Run from the repository root.

**Inner (during edits):**

```powershell
uv run pytest tests/test_screening_decision_contract.py -q
git diff --check
```

**Checkpoint (module complete):**

```powershell
uv run pytest tests/test_screening_decision_contract.py tests/test_screening_decision_integrity.py tests/test_screening_migration.py tests/unit/test_screening_prepare_stage.py -q
```

**PR candidate (`pr` stage, selected by `scripts/select_test_gate.py`):**

```powershell
uv run python scripts/select_test_gate.py --path src/scholar_harness/screening/decision_contract.py --path src/scholar_harness/agent_screen.py --stage pr
git diff --check
uv run pytest -q
uv run ruff check scripts/
```

**Closure (`closure` stage, `RELEASE` lane):**

```powershell
uv run python scripts/select_test_gate.py --path src/scholar_harness/screening/decision_contract.py --path src/scholar_harness/agent_screen.py --stage closure
uv run pytest -q
uv run pytest tests/conformance -q
uv run ruff check scripts/
uv run python scripts/generate_contract_baseline.py --check
uv run python scripts/generate_contract_schemas.py --check
uv run python scripts/generate_two_study_contract_fixture.py --check
uv run python scripts/generate_nexus_scholar_pins.py --check
```

The cross-platform CI matrix (ubuntu/windows/macos × Python 3.11/3.12) is executed by CI,
not locally.

**Known baseline failure that must NOT be attributed to this packet:** the two
`tools/scholar-search-kit/tests/test_enrichment.py` failures caused by the pre-existing
dirty `tools/scholar-search-kit/` tree.

---

## TOOLKIT_SYNC_AND_PIN_PLAN

**Not applicable — no toolkit change in this packet.** `tools/` is untouched, so no
canonical-kit merge, no `default_rev` bump, and no vendored-snapshot sync are required.
The pin check (`generate_nexus_scholar_pins.py --check`) must still pass unchanged, and
the pre-existing dirty `tools/scholar-search-kit/` files must be left exactly as they
are. This packet creates **no** dependency on the toolkit repair (K0), which is a
separate packet.

---

## WORKSPACE_AUDIT_EVENT

The `validate` command mutates the workspace (new report sidecar + `INDEX.md`
refresh). It must log exactly one event via
`scholar_harness.workspace.audit.log_event`:

| Field | Value |
|---|---|
| `action` | `SCREENING_VALIDATION` |
| `agent` | `agent_screen.validate` |
| `description` | states what was validated and the outcome, e.g. `"Validated 566 screening decision files against the workspace decision contract: 501 VALID / 65 DEBT / 0 BAD; 65 debt tags recorded; no producer file modified"` — counts must be the **recomputed** counts, not a restatement of a prior report |
| `inputs` | the decision files scanned + the contract config path |
| `outputs` | the report sidecar path (relative to the workspace) |
| `parameters` | the contract config path, tier vocabulary version |
| `metrics` | `files_scanned`, `valid`, `debt`, `bad`, `debt_tag_count` |
| `status` | `SUCCESS` when the scan completed and the report was written; `FAILED` when the scan refused (e.g. `REPORT_EXISTS`) or the contract config was unusable |

The journal must never be hand-edited. `log_event` owns append-only semantics and the
`INDEX.md` refresh.

---

---

## Amendment A — 2026-10-20, after reviewer round 1

The reviewer returned **CHANGES_REQUESTED**. Two items in this packet were
**wrong** and are corrected here; the rest of the corrections are additive scope
that the reviewer and the orchestrator agreed the packet should have carried.

### A1 — OUTPUTS: the default report path moved out of the scanned directory

The original OUTPUTS mandated `literature/screening/decision_contract_report.json`,
which is **inside** the directory the reader scans, while AC-24 says the reader
"never writes to the decisions directory". The two cannot both hold literally.

**Corrected:** the default report path is **`literature/screening_reports/decision_contract_report.json`** —
outside `literature/screening/`. AC-24 now holds as written. The report is still
written inside the workspace and is still a workspace mutation requiring an audit
event.

### A2 — G2: the tier rollup is stated, and advisory findings mark the file DEBT

The original G2 enumerated DEBT conditions but said nothing about advisories, which
is the silence the reviewer flagged (D2). The rule is now explicit:

> A file is `DEBT` when it carries **any** debt **or** advisory finding. An
> advisory-only file (e.g. unknown keys, over-length support) is `DEBT`, not
> `VALID`. Only structural findings make a file `BAD`.

This is the rule the demo driver used, and it restores **exact parity** with the
pilot's recorded artifact `v03_scr1_schema_debt_report.json`:
A1 `247 VALID / 36 DEBT`, A2 `254 VALID / 29 DEBT`, total **`501 / 65 / 0 BAD`**.

Rationale: an unknown key is a deviation from the frozen instrument's allowed field
list, and an over-length `one_line_support` violates the instrument's "one line"
requirement. Both deserve triage, not a clean bill. The previous behaviour
(advisory ≠ debt) produced `525 / 41` on the same corpus, which would have forced a
reconciliation between the pilot's recorded numbers and the tool's.

### A3 — G2 and the config shape: default file-name patterns follow the harness lane

The default patterns must match the lane the harness itself produces
(`batcher.py:136`, `:366`): `batch_{n:03d}_decisions.json` and `batch_{n:03d}.json`.
Any other layout — including the pilot's `calibration_v03/screening_scr1/` — is
expressed by a **contract config file**, not by changing defaults.

The tool must also make a total parent-resolution failure **loud**: a scan in which
no parent resolves must not be indistinguishable from a scan in which everything is
genuinely bad.

### A4 — Additive scope: a workspace-relative decisions directory

`cmd_validate` gains `--decisions-dir <workspace-relative-path>`, defaulting to
`literature/screening`. This is what allows the tool to read the pilot corpus
(`calibration_v03/screening_scr1/decisions/`) without moving a single file. The
flag is a per-invocation concern; the contract config stays per-workspace.

### A5 — Corrected worked example

The worked example in this packet quoted the pilot's `501 VALID / 65 DEBT / 0 BAD`.
That figure is correct **under the A2 rule** and is now the expected output of the
tool against the pilot corpus. Add a note that a 4-digit, family-suffixed,
`moderation_views`-parented layout requires a contract config, and that the
advisory rollup changes the file-level split by 24 files if it is reverted.

---

## Repair Round 1 — bounded findings from reviewer round 1

**Evidence invalidated by this repair:** the reviewer round's evidence for AC-24
(literal), the tier-rollup figures (D2), the default-pattern behaviour (D4), the
pilot-corpus reachability (D6), and the full-suite result (all of it — the repair
changes executable code, so the whole `pr` gate must be re-run).

| Finding | Severity | Required outcome |
|---|---|---|
| **D1** | MAJOR | The reader must not re-ingest its own artifacts. Exclude the report sidecar and the contract config **by name**, not only by the current output path. Add a regression test: run 1 with the default `--out`, run 2 with a different `--out` → the second run must report the same file count and the same tiers as the first. |
| **D2** | MINOR | Implement the A2 rollup (advisory → DEBT). State the rule in the module docstring and in the report itself (a `tier_rule` string). Re-verify against the pilot corpus: expect A1 `247/36`, A2 `254/29`, total `501/65`, per-tag counts unchanged. |
| **D3** | MINOR | Move the default report path to `literature/screening_reports/decision_contract_report.json` (A1). Update the affected test so it asserts the literal AC-24 wording. |
| **D4** | MINOR | Align the default patterns with the harness lane (A3) and make total parent-resolution failure loud. Add a test using harness-lane names (`batch_001.json` / `batch_001_decisions.json`). |
| **D5** | MINOR | Remove the invented `prompt_n_records` branch, or give it a fixture, a test, and a documented statement of who writes that key. Rename the emitted code so it says what it actually compares (a producer self-report vs the parent manifest), not "prompt". |
| **D6** | MINOR | Add `--decisions-dir <workspace-relative-path>` (A4), defaulting to `literature/screening`. Verify against the pilot corpus with an explicit contract config. |
| **D7** | P3 | Refuse before logging when the workspace root does not exist — a typo'd path must not materialise `audit/journal.jsonl` + `INDEX.md`. |
| **D8** | P3 | Name the five public names the docstring omits (`tag_prefix`, `TIERS`, `DEBT_PREFIXES`, `ADVISORY_PREFIXES`, `STRUCTURAL_CODES`), and add the reviewer's disambiguation line: the exported `DecisionContract` **type** is not the Contract v1 `contracts/` package. |

### Repair scope limits

- Changed paths stay inside the original ALLOWED_PATHS. The new
  `literature/screening_reports/` default is a **path string**, not a directory this
  task creates in any repository workspace.
- Do **not** touch `src/scholar_harness/contracts/**`,
  `screening/{collector,batcher,integrity,worker,report}.py`, `tools/**`,
  `workspaces/**`, `packaging/**`, `.agents/plugins/**`, `apps/**`.
- Do **not** modify the pre-existing dirty files.
- The pilot corpus under `workspaces/uav-crop-weed-v03/` is **read-only**; any
  verification run must use `--out` pointing outside the workspace, and the
  workspace must be byte-identical afterwards.
- Do not commit, push, or touch git remotes.

### Repair validation

```powershell
uv run pytest tests/test_screening_decision_contract.py -q
uv run pytest -q
uv run pytest tests/conformance -q
uv run ruff check scripts/
uv run python scripts/generate_contract_baseline.py --check
uv run python scripts/generate_contract_schemas.py --check
uv run python scripts/generate_two_study_contract_fixture.py --check
uv run python scripts/generate_nexus_scholar_pins.py --check
git diff --check
```

Plus a re-verification against the pilot corpus (read-only) reporting the A1/A2
family figures, and confirmation that `git status --porcelain workspaces/` is
unchanged.

---

## Amendment B — 2026-10-20, after reviewer round 2 (repair-delta review)

Reviewer round 2 verdict: **CHANGES_REQUESTED**. It confirmed **all eight** round-1
findings genuinely fixed, found **no scope creep**, and confirmed the pilot parity
independently (A1 247/36, A2 254/29, total 501/65/0 BAD, every per-tag count
identical). Four bounded items remain. This is the **final** coder-reviewer cycle.

### B1 — R1 (MAJOR): the default contract has no id-order authority

Round 1 made the defaults follow the harness lane (A3). The harness lane publishes
**no view artifact**, so the id-order check — which was gated on
`view_document is not None` — never ran. A decision file whose rows are **in the
wrong order** was classified `VALID`, while `parent_resolution.files_with_parents`
actively reported that parents *were* resolved. "Not checked" and "checked and in
order" were indistinguishable.

This is the defect class the tool exists to catch: the pilot quarantined exactly
this (`decisions_repair/batch_0040_decisions_A2_reorder_quarantine.json`).

**The parent batch is an id-order authority in both lanes:**

| Lane | Parent batch | Ordered list | Id key |
|---|---|---|---|
| harness | `batch_{n:03d}.json` | `papers[]` | `workspace_id` |
| pilot | `batch_0001.json` | `records[]` | `screening_id` |

The view is an optional **redaction overlay**, not the primary parent.

> **Critical correction from the reviewer — do not ship the naive fix.** The parent
> list and the rows can carry their ids under **different keys** (harness batch:
> `workspace_id`; canonical row id: `screening_id`). A fix that reads the parent's
> ids under `workspace_id` and compares them to `row["screening_id"]` compares
> `None` with `None` and **silently passes**. The id key must be resolved
> explicitly on each side, and the implementation must be **incapable of passing
> vacuously**.

**Required outcome:**

1. Build the authoritative ordered id list from the **view** when one is configured
   *and* resolved; otherwise from the **parent batch's** ordered record list
   (`records[]` / `papers[]`).
2. Resolve the row id under an explicit, configurable canonical id field (default
   `screening_id`); resolve the parent ids under the first key present among
   `screening_id` / `workspace_id` / `study_id`.
3. **Never silently pass.** If a parent list exists but ids cannot be extracted on
   either side, emit an explicit structural finding (e.g.
   `ID_ORDER_NOT_VERIFIABLE`) so "not checked" can never be reported as
   `VALID`-and-in-order. *This floor alone is the minimum acceptable fix; the full
   option 1+2 is preferred.*
4. A mismatch against the batch authority must carry a **machine-readable code
   distinct from** `ID_ORDER_MISMATCH_VS_VIEW`.
5. Tests: a **reordered harness-lane file under the default contract** must not come
   out `VALID`; the existing view-based `id_order_mismatch` test must keep passing.

### B2 — R2 (MINOR): the audit status must not say SUCCESS when nothing was verified

The scan-level `NO_PARENTS_RESOLVED` finding was surfaced in the report, on stderr
and in the metrics — but the journal status stayed `SUCCESS`. Worse, the **empty
scan** (no decision files at all) emitted **no finding whatsoever**, because the
finding was raised only when files were found. An empty run was indistinguishable
from a clean run of an empty corpus.

**Required status semantics:**

| Case | Status | Exit | Reason code |
|---|---|---|---|
| (i) files found, **no parent resolved** | `FAILED` | non-zero | `NO_PARENTS_RESOLVED` in metrics **and** description |
| (ii) **no decision files at all** | `FAILED` | non-zero | a **distinct** code (e.g. `NO_DECISION_FILES`), present in the report's `scan_findings` **and** the journal metrics |
| (iii) normal scan, DEBT and/or BAD present | `SUCCESS` | 0 | — |

Case (ii) is deliberately `FAILED`: an empty directory cannot be distinguished from
a **mis-pointed `--decisions-dir`**, which is exactly the pilot's layout trap (the
pilot's decisions live one level down). The reason text must make the cause
legible, not mysterious.

### B3 — N1 (MINOR): the `--out` help still advertises the pre-A1 default path

`agent_screen.py:165-166` still says `literature/screening/decision_contract_report.json`;
the actual default is `literature/screening_reports/decision_contract_report.json`.
Introduced by the D3/A1 repair — the default moved and the help did not. The
existing assertion (`"literature/screening" in stdout`) is satisfied by the stale
string and did not catch it.

**Required outcome:** correct the help string, and **pin the full path** in the test
so the stale value cannot pass again.

### B4 — N2 (P3): the advisory vocabulary comment contradicts the A2 rollup

`decision_contract.py:158` still reads *"Advisory: reported, never a defect, never a
tier change."* Under A2 an advisory **does** change the tier (to `DEBT`). This is
the exact statement Amendment A2 inverted, left standing in the normative
vocabulary block.

**Required outcome:** one-line rewrite — *"advisory findings mark the file `DEBT`,
never `BAD`."*

---

## Repair Round 2 — bounded findings from reviewer round 2 (final cycle)

**Evidence invalidated by this repair:** the whole `pr`/`closure` gate set. The
repair changes executable code and the report's status semantics, so the full
suite, conformance, baseline checks and the pilot parity re-verification must all
be re-run.

| Finding | Severity | Required outcome |
|---|---|---|
| **R1** | MAJOR | B1 items 1–5. |
| **R2** | MINOR | B2's status/exit/reason-code table. |
| **N1** | MINOR | B3. |
| **N2** | P3 | B4. |

### Repair scope limits (unchanged from round 1)

- Changed paths stay inside the original ALLOWED_PATHS.
- Do **not** touch `src/scholar_harness/contracts/**`,
  `screening/{collector,batcher,integrity,worker,report}.py`, `tools/**`,
  `workspaces/**`, `packaging/**`, `.agents/plugins/**`, `apps/**`,
  `.github/workflows/**`.
- Do **not** modify the pre-existing dirty files.
- The pilot corpus is **read-only**; any verification run must use `--out` outside
  the workspace, and the workspace must be byte-identical afterwards.
- Do not commit, push, or touch git remotes.

### Repair validation

```powershell
uv run pytest tests/test_screening_decision_contract.py -q
uv run pytest -q
uv run pytest tests/conformance -q
uv run ruff check scripts/
uv run python scripts/generate_contract_baseline.py --check
uv run python scripts/generate_contract_schemas.py --check
uv run python scripts/generate_two_study_contract_fixture.py --check
uv run python scripts/generate_nexus_scholar_pins.py --check
git diff --check
```

Plus: the **pilot parity re-verification** (read-only) still reporting
A1 `247/36`, A2 `254/29`, total `501/65/0 BAD` with unchanged per-tag counts; and a
**reordered-file regression** under the default contract that must not come out
`VALID`.

---

## Context capsule

```yaml
task: T-D0D2
delivery_lane: RELEASE
owner_repo: nexus-scholar-org/nexus-scholar-harness
base_sha: c10d2819e92556cabd8124e918a1bb672504c9ec
head_sha: c10d2819e92556cabd8124e918a1bb672504c9ec   # + uncommitted working-tree changes
allowed_paths:
  - src/scholar_harness/screening/decision_contract.py
  - src/scholar_harness/screening/__init__.py
  - src/scholar_harness/agent_screen.py
  - tests/test_screening_decision_contract.py
  - tests/fixtures/screening_decision_contract/**
immutable_boundaries:
  - src/scholar_harness/contracts/**            (frozen Contract v1)
  - src/scholar_harness/screening/collector.py  (Contract v1 publication path)
  - src/scholar_harness/screening/batcher.py
  - src/scholar_harness/screening/integrity.py
  - tools/**                                    (no toolkit change)
  - workspaces/**                               (read-only reference)
  - packaging/**, .agents/plugins/**            (no pin/vendor change)
  - apps/**                                     (no UI change)
acceptance_ids: [AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10, AC-11,
                 AC-12, AC-13, AC-14, AC-15, AC-16, AC-17, AC-18, AC-19, AC-20, AC-21,
                 AC-22, AC-23, AC-24, AC-25, AC-26, AC-27, AC-28, AC-29, AC-30, AC-31,
                 AC-32, AC-33, AC-34, AC-35]
open_findings: [R1, R2, N1, N2]   # repair round 2 (final cycle)
known_baseline_failures:
  - tools/scholar-search-kit/tests/test_enrichment.py::test_hydrate_from_openalex_success
  - tools/scholar-search-kit/tests/test_enrichment.py::test_hydrate_missing_abstracts_fallback_to_openalex
  - note: pyproject testpaths = ["tests"], so these are NOT collected by `uv run pytest -q`
evidence:
  - command: uv run python scripts/generate_contract_baseline.py --check
    commit: c10d281
    result: pass - "Contract baseline current"
  - command: uv run python scripts/generate_nexus_scholar_pins.py --check
    commit: c10d281
    result: pass - "[OK] packaging/nexus-scholar/nexus_scholar_pins.json is in sync with plugins.json"
  - command: uv run pytest -q
    commit: c10d281
    result: pass - green, no failures (deprecation warnings only)
  - command: uv run pytest -q -o addopts=   # reviewer round 1
    commit: working tree @ round 1
    result: pass - 1528 passed, 6 skipped (baseline 1466 passed, 6 skipped; +62 new tests)
  - command: uv run pytest tests/conformance -q -o addopts=
    commit: working tree @ round 1
    result: pass - 169 passed, 2 skipped
  - command: uv run pytest -q -o addopts=   # reviewer round 2
    commit: working tree @ round 1
    result: pass - 1540 passed, 6 skipped (round 1: 1528; +12 new tests)
  - command: reviewer round 2 delta review
    commit: working tree @ round 1
    result: CHANGES_REQUESTED - D1..D8 all VERIFIED FIXED, no scope creep, pilot parity confirmed independently (501/65/0)
next_gate: inner
stable_sources:
  - docs/architecture/test_gate_policy.md
  - docs/architecture/DEVELOPER_COMPASS.md (§3 hard invariants, §7 required validation)
  - src/scholar_harness/screening/integrity.py
  - workspaces/uav-crop-weed-v03/_drivers/v03_scr1_schema.py
```

## Follow-ups deliberately NOT in this packet

Recorded, not dispatched:

- **C-1** (acceptance `DEBT` tier) — this packet's `VALID`/`DEBT`/`BAD` tiers are
  **reader-local** and must not be assumed to be the acceptance vocabulary. C-1 must
  align or explicitly supersede them. This packet exposes all tier names from one
  place so that alignment is a single-file change.
- **D-1** (verification lane) — blocked on D-0/D-2 landing.
- **HCM-1** (the promotion rule itself) — the rule that licenses this promotion is
  recorded in `docs/architecture/decisions/`; that ADR is a separate docs-only task.
- **D-4** (lane-split gate) and **B-D1** (near-twin pass) — separate packets.

### Recorded at reviewer round 3 (APPROVE) — must not be dropped

- **`--fail-on-bad` (opt-in flag, default off).** Today the exit code means only
  *"did the scan do its job?"*: exit 0 = the scan completed, exit 1 = the scan could
  not complete or verified nothing. A scan that finds `BAD` files exits 0. That is
  correct against this packet (G9 constrains **collection**, not the validator), but
  a consumer that reads only the exit code is not served. **Required rule:** add an
  opt-in `--fail-on-bad` flag that exits non-zero when `bad > 0`, keeping the default
  semantics for humans and giving scripts strict behaviour on demand. The strict
  machine channel already exists today: journal `metrics.bad`, the report's
  `files[].structural`, and the stdout tier line.
- **`NO_PARENTS_RESOLVED` can misattribute the cause (reviewer finding F3).** A
  corpus whose only decision file returns early (unparseable / BOM / no rows key /
  unsupported schema major) never reaches the parent stage, so the scan-level
  finding says *"the parent locations do not match the contract"* when the real
  defect is that the decision files are corrupt. The verdict is still correct
  (`FAILED`, exit 1) and the truthful per-file cause is in the same output, so this
  is **not** a false green. **Required outcome:** distinguish "parents not resolved"
  from "parents not attempted" — set the parent-resolution marker on the early-return
  paths, or have the report count only files that reached the parent stage — so
  `NO_PARENTS_RESOLVED` fires only when parents were actually sought and none
  resolved.
