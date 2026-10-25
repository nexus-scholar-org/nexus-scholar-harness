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
