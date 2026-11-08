# M7b-guideline: reporting follows a guideline chosen in the protocol
Branch: `dev/m7b/guideline` · Lane: **RELEASE** (protocol identity and the methods paragraph; `test_gate_policy.md` §lanes) · Status: IN PROGRESS · Started: 2026-11-08

Why: this is step 11 of the researcher's beta plan of 2026-11-07. Decision: [2026-11-08, Reporting follows a guideline chosen in the protocol](../../decisions.md). The protocol's `method` block gains an optional `reporting` key (`prisma-2020`, `prisma-scr` or `none`). When the key is absent it comes from `playbook_type`. It changes only the screen labels and one methods sentence.

## Definition of done
- [ ] **G1. The key.** `MethodConfig.reporting` is optional and defaults to `None`. An absent key is left out of the canonical JSON, so no fingerprint moves. The schema is regenerated.
  - Tests: a block without `reporting` hashes exactly as on `main`; a block with `reporting` hashes it; unknown values are refused.
- [ ] **G2. The derivation.** `effective_method` resolves the guideline from the key if present, otherwise from `playbook_type` (the decision's table), otherwise `prisma-2020`. It reports `reporting_source` (`protocol` or `playbook`).
  - Test: each playbook type gives its default; a protocol override wins.
- [ ] **G3. New workspaces state it.** Genesis writes the derived value into the block.
  - Test: a scoping-review workspace gets `prisma-scr`.
- [ ] **G4. API.** `GET /settings` carries `reporting` (read-only), so the screens can label themselves. The contract row and the fixtures are updated.
- [ ] **G5. The methods paragraph** adds the guideline sentence after the source sentence (no sentence for `none`). `figures.method` carries `reporting` and `reporting_source`.
  - Tests: all three values; the numbers-trace invariant still holds.
- [ ] **G6. Labels.** Publish's preview heading and Export's counts heading and language note follow the guideline. Specs 09 and 10 are amended first.
  - vitest for the three values in en, plus copy completeness in fr and ar.
- [ ] **Gate:** RELEASE closure on the final executable commit, including `generate_contract_baseline.py --check`.
- [ ] **Review:** the milestone-reviewer returns APPROVE.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |

## Decisions
- [2026-11-08, Reporting follows a guideline chosen in the protocol](../../decisions.md) (researcher, accepted 2026-11-08).

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |

## Deferred
- PRISMA-ScR's "sources of evidence" wording in the counts. It belongs to the parked PRISMA-ScR checklist work.
- Renaming `prisma_report.json`. It is a publication artifact, so the name stays under every guideline.
