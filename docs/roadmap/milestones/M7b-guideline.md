# M7b-guideline: reporting follows a guideline chosen in the protocol
Branch: `dev/m7b/guideline` · Lane: **RELEASE** (protocol identity and the methods paragraph; `test_gate_policy.md` §lanes) · Status: IN PROGRESS · Started: 2026-11-08

Why: this is step 11 of the researcher's beta plan of 2026-11-07. Decision: [2026-11-08, Reporting follows a guideline chosen in the protocol](../../decisions.md). The protocol's `method` block gains an optional `reporting` key (`prisma-2020`, `prisma-scr` or `none`). When the key is absent it comes from `playbook_type`. It changes only the screen labels and one methods sentence.

## Definition of done
- [x] **G1. The key.** Done 2026-11-08: the schema was regenerated, and the contract baseline, schemas and goldens `--check` pass unchanged. Tests in `tests/kits/protocol/test_method_block.py` failed first. `MethodConfig.reporting` is optional and defaults to `None`. An absent key is left out of the canonical JSON, so no fingerprint moves. The schema is regenerated.
  - Tests: a block without `reporting` hashes exactly as on `main`; a block with `reporting` hashes it; unknown values are refused.
- [x] **G2. The derivation.** Done 2026-11-08: `PLAYBOOK_REPORTING` in `screening/method.py`. Tests: `tests/unit/test_effective_method.py`, which failed first. `effective_method` resolves the guideline from the key if present, otherwise from `playbook_type` (the decision's table), otherwise `prisma-2020`. It reports `reporting_source` (`protocol` or `playbook`).
  - Test: each playbook type gives its default; a protocol override wins.
- [x] **G3. New workspaces state it.** Done 2026-11-08. Tests: `tests/inception/test_new_workspace_method.py`, which failed first. Genesis writes the derived value into the block.
  - Test: a scoping-review workspace gets `prisma-scr`.
- [x] **G4. API.** Done 2026-11-08: `reporting` and `reporting_source` are derived, never stored, and `PUT` refuses them with 422 (the body forbids extra keys). Contract row updated; the `settings_default` fixture gained two fields. Test: `tests/console/test_method_settings.py`. `GET /settings` carries `reporting` (read-only), so the screens can label themselves. The contract row and the fixtures are updated.
- [x] **G5. The methods paragraph** adds the guideline sentence after the source sentence (no sentence for `none`). `figures.method` carries `reporting` and `reporting_source`.
  - Tests: all three values; the numbers-trace invariant still holds. Done 2026-11-08 (`tests/console/test_methods_method_block.py`, which failed first). Review 1 corrected this: the invariant did **not** hold for `prisma-2020`, because "PRISMA 2020" carries a number and the earlier tests only exercised the scoping path. `figures.method.reporting_label` ("PRISMA 2020" or "PRISMA-ScR") now carries the name, and the numbers-trace and banned-word invariants run for all three guidelines.
- [x] **G6. Labels.** Done 2026-11-08, with copy from the spec 09 and 10 amendments. Publish reads `reporting` from `GET /settings`, and an engine without the field reads as PRISMA 2020. Export reads it from the bound publication's `figures.method.reporting`, so its heading and the paragraph always agree. Two wording refinements from the spec writer were accepted: "flow diagram" replaces "PRISMA box", and the `none` heading is "Counts of the published screening". Two older Export tests now use the PRISMA 2020 caption. vitest `publish.reporting` and `export.reporting` failed first; the full vitest suite passes 283/283. Publish's preview heading and Export's counts heading and language note follow the guideline. Specs 09 and 10 are amended first.
  - vitest for the three values in en, plus copy completeness in fr and ar.
- [x] **Gate:** RELEASE closure on the final executable commit, including `generate_contract_baseline.py --check`.
- [ ] **Review:** the milestone-reviewer returns APPROVE.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |

## Decisions
- [2026-11-08, Reporting follows a guideline chosen in the protocol](../../decisions.md) (researcher, accepted 2026-11-08).

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner | per item | targeted pytest/vitest per item | each red before, green after | seconds |
| closure (RELEASE) | `37a2057` | contract baseline, contract schemas, two-study fixture, canonical goldens and protocol schema `--check`; ruff; `git diff --check` | all pass | |
| closure (RELEASE) | `37a2057` | `pytest -q -n auto` | **4493 passed, 15 skipped, 0 failed** | 6 m 06 s |
| closure (RELEASE) | `37a2057` | `uv build --wheel` | `nexus_scholar-1.1.0b2-py3-none-any.whl` | |
| closure (RELEASE) | `37a2057` | typecheck, vitest, `next build`, Playwright (light and dark) | tsc clean; vitest **283/283**; build clean; Playwright **172 passed, 1 failed, 13 skipped**. The failure was `locale-routing.spec.ts` N2 (dark): `html lang` read null once. Re-run `--repeat-each=3`: **48/48 passed**. This branch does not touch locale routing | 4 m 42 s |

## Deferred
- **Import screen copy** (`screening-import.tsx`, review follow-up). "PRISMA asks for it" and "Counts for your PRISMA flow diagram" still read PRISMA under every guideline. Out of scope here, which covered Publish and Export only.
- **The golden run's methods paragraph will now say PRISMA-ScR.** Every committed UAV workspace is `SCOPING_REVIEW`, and the decision intends this.
- **No protocol** gives `reporting_source: "defaults"` (review 3), and `EffectiveMethod` has no silent defaults (review 4).
- PRISMA-ScR's "sources of evidence" wording in the counts. It belongs to the parked PRISMA-ScR checklist work.
- Renaming `prisma_report.json`. It is a publication artifact, so the name stays under every guideline.
