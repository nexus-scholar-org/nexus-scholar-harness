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
7. Charting: two competing drafts exist — pilot `charting sidecar v0.2` (state-coupled envelope cells, fingerprint-const bound) and v0.3 draft hosted here (per-dimension domain-enum-rich rows, no fingerprint const, no state coupling). The v0.3 sidecar is DRAFT; pilot v0.2 sidecar remains normative for anything charted in the parent workspace. Known v0.3 draft gap: evidence_state↔content conditional coupling is NOT enforced (synthetic negative N1 accepted) — import the v0.2 cell logic before freeze or consciously accept the weaker binding.
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
| INC-03 (flagged in §5 above) | **Freeze the bytes as-is**; record the flaw as an accepted limitation | Preserves the criteria hash that all 566 decision files attest. Publication/export of the protocol text is **blocked** until reviewer consent is recorded or the names are redacted by an editorial amendment (no re-screen required for redaction) |
| Reviewer design | Option C retained as the design; consent **not obtained**; independent human review **not claimed** | Protocol freeze ≠ screening confirmation; `HumanConfirmation@1` remains unsigned |
| Charting binding | v0.3 draft `charting.schema.json` frozen **with** accepted limitation F1 | F1 (no `evidence_state`↔content coupling) is unresolved: **no charting rows may be accepted for the v0.3 pilot** until repaired; charting pilots continue on the v0.2 sidecar |
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

**Status: FINAL AGENT DECISIONS — NOT HUMAN-CONFIRMED.** No protocol byte,
criteria byte, or charting byte changed; the frozen instrument and the
`9ae1f97d…b86f` criteria hash that all 566 decision files attest are untouched.

Authority: explicit user instruction 2026-10-29 delegating the outstanding
researcher decisions ("i approve your decision so take them instead of me and
finish the freeze"), plus the follow-up screening instruction. Recorded as a
**delegated mechanical decision**, not authenticated human approval.
`HumanConfirmation@1` remains **unsigned**.

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
