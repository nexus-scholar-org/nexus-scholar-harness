# Protocol amendments

## v0.2 -> v0.3 (researcher-requested revision; provisional, hosted in a new workspace)

Revision timestamp: 2026-10-17 (compile executed in `workspaces/uav-crop-weed-v03/`)
Prior fingerprint: `sha256:a1fd8d2a82e0a5fca77deabbad360a1d8190d2d017d3ffa38342d8ac7ff73451` (parent workspace `../uav-crop-weed-reliability/`)
New fingerprint: `sha256:f81e6c58aefb3159cb679ca87c4a83382dca199e0b02bb12ac409c15f8a4f755`
Author: v0.3 content drafted in conversation at researcher request; orchestrator agent transcribed intent and executed the deterministic compile here. This records authorship, not authenticated scientific approval or protocol freeze.

Changes (v0.2 -> v0.3):

1. `metadata.target_venue_type`: "Undecided; provisional scoping-review protocol" -> stated Q1 agricultural-informatics / remote-sensing target (e.g., COMPAG, Remote Sensing, ISPRS) with PRISMA-ScR framing.
2. `epistemology.unit_of_analysis` and RQ framing expanded: explicit collapse of preprint/conference/dataset-report versions into study-family primary rows while keeping separate evaluation-setting rows per dataset/split/shift/target-data-use condition.
3. Search concepts expanded (UAV: +uncrewed aerial vehicle, remotely piloted aircraft, aerial imagery, orthomosaic; weed: + site-specific weed management, precision weeding, herbicide prescription; mapping: + monitoring, localization, identification, discrimination).
4. Exclusion categories now carry reason codes aligned to the screening engine: EXC-01 WRONG_PLATFORM (with proximal/ground dataset list), EXC-02 WRONG_TASK (with explicit non-target tasks), EXC-03 WRONG_REPORT_TYPE (with the safeguard that abstract=null or failed retrieval is NOT this exclusion), EXC-04 OUTSIDE_DATE_LANGUAGE.
5. INC-03 now embeds the Option C screening design (single lead reviewer confirming agent triage, ~10% random + boundary-exclude verification by two named co-reviewers). FLAGGED (orchestrator opinion, pending researcher decision): process/administrative text inside an eligibility criterion mixes eligibility with workflow administration and embeds unconsented reviewer names in an artifact headed for a public-bound branch; recommend moving that sentence to a screening-design column/section before freeze. Consent gates (demo Scene 9) are unchanged.
6. `golden_seeds`: present in the hand-drafted v0.3 `protocol.json` but dropped by the deterministic compiler (by design); seeds carried in `SEARCH_STRATEGY.md` here + pilot calibration sentinels and consumed via `scholar-search validate-query`. A passthrough change to the compiler is a kit-repo stream (ownership gate; parked).
7. Charting: pilot `charting sidecar v0.2` (state-coupled envelope cells, fingerprint-const bound) remains normative for anything charted in the parent workspace. The v0.3 line was drafted here with per-dimension domain-enum-rich rows but no state coupling; that gap (F1) was **repaired and frozen as v0.3.1 on 2026-10-31**: `evidence_state` now governs content and provenance, the v0.2 cell logic was imported as per-dimension conditional shapes, and the negative matrix refuses every populated-under-absence case. See `validation_v031.json`.
8. No studies were screened under v0.3, so no rescreening obligations arise. v0.2-era artifacts everywhere remain untouched and byte-preserved.

Machine gate: strict validation VALID (0 errors, 0 warnings), deterministic recompile identical, canonical fingerprint recorded, canonical draft-vs-compiled divergence list recorded in `validation.json`.

## v0.3 freeze (2026-10-29)

**Status: FROZEN.** No field of `protocol.json` changed. The frozen instrument is
the compiled bytes at `sha256:f81e6c58aefb3159cb679ca87c4a83382dca199e0b02bb12ac409c15f8a4f755`,
rendered criteria at `9ae1f97dc0c9857bb59eb0025924f2dd104d2c41eca2777089b22eecad90b86f`,
charting schema at `02eaf2cee7af43390ab91b11e1831a4d98fdb0c7f99b9ef113abd69111cace85`.

Authority: explicit user instruction 2026-10-29 delegating the outstanding
researcher decisions. This is a **delegated decision recorded mechanically**, not
authenticated human approval and not a claim of independent human screening.
Basis: `EVT-20261017191328-03266a`, freeze-path step 2.

Decisions taken at freeze:

| Item | Decision | Recorded consequence |
|---|---|---|
| Final cutoff | `2026-10-17T23:59:59Z` (last executed search/harvest day, R3/r3d lineage) | Window end is now recorded; `protocol.json` still says "through the recorded final search cutoff", which resolves to this date |
| INC-03 (flagged in §5 above) | **Freeze the bytes as-is**; record the flaw as an accepted limitation | Preserves the criteria hash that the decision artifacts attest. **Resolved 2026-10-31:** both named co-reviewers consented to be published with their role, so the publication/export block on the frozen protocol text is **lifted**. Frozen bytes are unchanged; the workflow-inside-eligibility coupling remains a recorded quality limitation. See [`consent/INC-03_consent_and_conduct_record.md`](consent/INC-03_consent_and_conduct_record.md) |
| Reviewer design | Option C **executed** per researcher attestation; consent **recorded 2026-10-31**; independent third-party review of the whole corpus **not claimed** | Protocol freeze ≠ screening confirmation. A `HumanConfirmation@1` signature exists (2026-10-31, Mouadh BEKHOUCHE, 283 artifacts / 14,150 decisions, fingerprint `e1f51ffe…f876800`); the signer is the researcher, so this records reviewed acceptance, **not** independent third-party review. Co-reviewer verification is recorded separately in [`consent/INC-03_consent_and_conduct_record.md`](consent/INC-03_consent_and_conduct_record.md) as attested, not stored as a sampling log |
| Charting binding | v0.3.0 frozen 2026-10-29 with accepted limitation F1; **repaired in v0.3.1 on 2026-10-31** | F1 (no `evidence_state`↔content coupling) is **repaired**: the schema now couples state to values and provenance, with a 44-case matrix (13 dimensions × populated-under-absence, targeted negatives, one v0.3.0-accepted regression fixture). SHA-256 `91dbe0c8f81034ccb5f7eea903a11d3d96e9a50bc42914eea6ec7d0fe7596b42`. Charting rows may now be produced under v0.3.1 (none accepted yet) |
| Search completeness | HTTP 429 S2 quota wall recorded; freeze r3 lineage | PRISMA-ScR search log must state the provider wall |

Gates re-verified on 2026-10-29:

- `scholar-protocol compile intent.json` → **byte-identical** to `protocol.json`
  (determinism holds; nothing was hand-edited).
- `scholar-protocol validate protocol.json --strict` → **VALID**, 0 errors, 0 warnings.
- `scholar-protocol fingerprint` → `sha256:f81e6c58…f755`;
  `identity` → `PRT-f81e6c58aefb3159cb679ca87c4a8338`.
- Render parity: a fresh `render-criteria` differs from the stored
  `SCREENING_CRITERIA.md` by **one trailing blank line** (5350 vs 5349 bytes);
  eligibility text is identical. The stored bytes were deliberately **not**
  re-rendered, because the 566 decision files attest `9ae1f97d…b86f`.

Not done here (and deliberately so): no screening confirmation, no `PENDING`
resolution, no reviewer consent, no protocol-text export. The freeze authorizes
scope; it does not validate results.

## v0.3 screening finalization (2026-10-29)

**Status as of 2026-10-29: FINAL AGENT DECISIONS — NOT HUMAN-CONFIRMED.** Superseded by the 2026-10-31 signature and consent records (below). No protocol byte,
criteria byte, or charting byte changed; the frozen instrument and the
`9ae1f97d…b86f` criteria hash that all 566 decision files attest are untouched.

Authority: explicit user instruction 2026-10-29 delegating the outstanding
researcher decisions ("i approve your decision so take them instead of me and
finish the freeze"), plus the follow-up screening instruction. Recorded as a
**delegated mechanical decision**, not authenticated human approval.
`HumanConfirmation@1` was signed on **2026-10-31** by **Mouadh BEKHOUCHE** (PhD student, University of Oum El Bouaghi, lead_reviewer) over all 283 decision artifacts and 14,150 decisions, all recorded `confirmed` with no overrides. Record: `literature/screening/HUMAN_CONFIRMATION.json`.

### Resolution rule (deterministic, applied by `_drivers/v03_scr1_finalize.py`)

| # | Lane condition | Final decision | Rows |
|---|---|---|---:|
| 1 | A1 == A2 == INCLUDE | INCLUDE (`mutual_include`) | 588 |
| 2 | A1 == A2 == EXCLUDE | EXCLUDE (`mutual_exclude`) | 12,357 |
| 3 | arms disagree → third lane terminal | as the third lane ruled (`third_lane`) | 814 (40 INC / 641 EXC / 133 PENDING) |
| 4 | still PENDING, usable abstract present | pass-2 re-screen (`pass2`) | 178 (16 INC / 162 EXC) |
| 5 | still PENDING, no usable abstract | **EXCLUDE, `NO_USABLE_ABSTRACT_NOT_RETRIEVED`** (`not_retrieved`) | 346 |

Result: 14,150 records screened → **644 INCLUDE / 13,506 EXCLUDE**, of which
346 are *not retrieved* (no usable abstract). PRISMA: 14,413 identified − 263
duplicates = 14,150 screened.

### DEV-01 — no-abstract exclusion (recorded deviation)

The researcher instruction was: re-screen the undecided records that have
abstracts, record those as final, and exclude the rest with a note. Applied
literally, this excludes 346 records that have no usable abstract instead of
leaving them `PENDING`. That **deviates** from INC-02/EXC-03 ("an incomplete
provider abstract or failure to retrieve full text is not an exclusion") and
from the Pass-1 guardrail. The deviation is disclosed here, carried as
`deviation: DEV-01` on every affected record, counted separately in
`prisma_report.json` (`records_not_retrieved`), and *not* buried in the
substantive exclusion reasons. Removing DEV-01 would return those 346 records to
`PENDING`; nothing else in the corpus depends on it.

### Residual imperfections (recorded, not repaired)

- One mutual-EXCLUDE record (`SCI-003479`) carries no machine-readable reason
  code in either arm; it is counted as `UNSPECIFIED` rather than back-filled by
  inference.
- 373 A1/A2 INCLUDE-vs-EXCLUDE disagreements were settled by the third lane, not
  by a human adjudicator.
- `OUT_OF_SCOPE` (9), `BOUNDARY_AMBIGUOUS_PLATFORM` (4), and
  `MODERATION_TITLE_ONLY_EXCLUDE` (145) are screener vocabulary that falls
  outside the four protocol exclusion criteria; they are reported verbatim.
- This is **not** a Contract-v1 published generation: there is no
  `MANIFEST.json`, no `verified.json` with `workspace_id`, no corpus snapshot,
  and no `publication_approval.json`. The artifacts are pilot outputs written
  directly by the driver and labeled `FINAL_AGENT_UNCONFIRMED`.

### Artifacts

| File | Content |
|---|---|
| `literature/included.json` | 644 included records (document + screening) |
| `literature/excluded.json` | 13,506 excluded records, provenance per row |
| `literature/screening/final_decisions.json` | all 14,150 final decisions |
| `literature/screening/summary.json` | counts, lanes, reasons, deviations |
| `literature/prisma_report.json` | PRISMA counts (incl. not retrieved) |
| `literature/prisma_screening_report.md` | human-readable report + Mermaid |
| `calibration_v03/screening_scr1/final_lane/decisions_pass2.json` | pass-2 re-screen, 178 rows |

## v0.3 canonical screening export for the console and UI (2026-10-30)

### What was added

The finalized corpus was readable through the contract reads
(`literature/included.json`, `literature/excluded.json`) but the console's
*screening* surface and the Research UI's live screening screen read the
harness's canonical batch layout, which this pilot never produced: its dual-code
decision files live under `calibration_v03/screening_scr1/` in the calibration
schema (`records` / `screening_id`), not as `batch_NNN.json` + `batch_NNN_decisions.json`.

A deterministic driver,
`_drivers/v03_canonical_screening_export.py`, now writes that derived view into
`literature/screening/`:

| File | Content |
|---|---|
| `MANIFEST.json` | 283 batches, 14,150 papers, run id `UAV-SCREEN-SCR1-20261018` |
| `batch_001.json` … `batch_283.json` | 50 screened records each, in source batch order |
| `batch_001_decisions.json` … `batch_283_decisions.json` | one final decision per record |

### What this is not

- **Not a new screening run.** No record was re-screened. Each decision is copied
  from `literature/screening/final_decisions.json`; each paper from the source
  batch's `records`; identifiers, criteria references, lane and reason code are
  copied, never re-derived.
- **Not a Contract-v1 published generation.** The export has no artifact
  registry, no accepted corpus snapshot, no `verified.json`, and no publication
  approval. The console therefore reports batch coverage as
  `WORKER_PARENT_UNRESOLVED` (no accepted parent artifact) and the publication
  status stays `LEGACY_UNVERIFIED`. The earlier statement in this file that "there
  is no `MANIFEST.json`" describes the finalization event of 2026-10-29; this
  derived export did not exist then and authorizes nothing.
- **Human confirmation is a separate record.** `decision_status` remains
  `FINAL_AGENT_UNCONFIRMED` because the decisions were agent-made, but
  `HumanConfirmation@1` was signed on 2026-10-31 over all 283 decision
  artifacts / 14,150 decisions (`literature/screening/HUMAN_CONFIRMATION.json`).
  This derived export is one of the hashed inputs; the export still authorizes
  nothing beyond what that confirmation binds.

### Provenance carried by every emitted file

Each batch, each decisions sidecar, and `MANIFEST.json` carry a
`derived_export` block naming the source directory, the criteria hash
(`9ae1f97d…b86f`), the protocol fingerprint (`sha256:f81e6c58…f755`), the
decision status, and `accepted_parent_artifact: false`.

### Reversibility

`git rm -r --cached` + deletion of the generated files returns the workspace to
its 2026-10-29 state; nothing else references them. Re-generating is a single
deterministic command:

```
uv run python workspaces/uav-crop-weed-v03/_drivers/v03_canonical_screening_export.py --force
```

## Open draft proposals (2026-10-31, not applied)

Two open items now have a written proposal under `proposals/`. Neither changes
the frozen instrument, the criteria, the 283 decision artifacts, or the signed
`HumanConfirmation@1`; both need a researcher decision before anything is
applied.

| Proposal | Open decision | Governing constraint |
| :--- | :--- | :--- |
| [`proposals/INC-03_redaction_amendment.md`](proposals/INC-03_redaction_amendment.md) | **Decided 2026-10-31 — Option A (consent).** Record: [`consent/INC-03_consent_and_conduct_record.md`](consent/INC-03_consent_and_conduct_record.md) | the names are embedded in every hashed batch file; the frozen instrument was not edited |
| [`proposals/F1_evidence_state_repair.md`](proposals/F1_evidence_state_repair.md) | freeze a v0.3.1 charting schema that couples `evidence_state` to content/provenance | no charting row may be accepted until F1 is repaired |

## Post-freeze resolutions (2026-10-31)

- **Screening confirmation signed.** `HumanConfirmation@1` by Mouadh BEKHOUCHE
  over all 283 decision artifacts / 14,150 decisions, no overrides,
  `retrospective: false`, fingerprint `e1f51ffe…f876800`. Decisions keep their
  `FINAL_AGENT_UNCONFIRMED` provenance; the confirmation is a separate record.
- **INC-03 consent recorded.** Both named co-reviewers consented (2026-10-31) to
  be published with their role; the Option C conduct is attested as executed.
  The publication block is lifted without editing the frozen instrument. No
  hash changed.
- **Charting F1 repaired and frozen as v0.3.1.** All four design decisions were
  taken (tri-state booleans, absence enums removed from `data_availability` /
  `code_availability`, two anchors + narrative for `conflicting`, publication
  type kept required). SHA-256 `91dbe0c8f81034ccb5f7eea903a11d3d96e9a50bc42914eea6ec7d0fe7596b42`; the v0.3.0 bytes are retained as
  `audit/charting_schema_v030_superseded.json`. Record:
  [`validation_v031.json`](validation_v031.json); matrix:
  `audit/charting_validation_matrix_v031.json` (44/44). No charting row has been
  charted under it yet.
- **Still open:** a confirmed export with real synthesis content (the export gate
  itself is proven).

`validation.json` is the **2026-10-29 protocol freeze snapshot** and still lists
the confirmation, consent, and F1 gap as outstanding. It is kept as-is on purpose:
it records what was true at freeze. The resolutions above supersede it, and the
charting instrument has its own freeze record in `validation_v031.json`.
