# M10a-search-quality Search quality and database choice
Branch: dev/m10a/search-quality · Lane: **RELEASE** (the probe and run bodies gain public HTTP fields, the MCP `recon_probe` and the CLI wizard send a different query, and the arXiv translation is a `scholar_search` change that Discovery shares; `test_gate_policy.md:43-48`, `DEVELOPER_COMPASS.md:93-94`; precedents M3h, M4c, M4d) · Status: IN PROGRESS · Started: 2026-11-14

First milestone of "Assisted inception" (plan §6, decisions 2026-11-14). Base: `origin/main` at `a0191cc6`. No language model anywhere in this milestone.

Why: in the strict run of 2026-11-13 (topic "UAV crop-weed mapping"), Explore returned nothing useful. A 19-word topic sentence was sent unchanged; OpenAlex and Semantic Scholar returned 0 of 0 and the screen called them "answered"; Crossref and arXiv matched any single word; the 25-paper sample was cut by database name; the Direction step proposed three generic directions.

Out of scope: the proposal mechanism, any assistant, critic or chat, the lighter-screens redesign, exclusion reason categories, matrix columns, wording fixes on the Review step, the empty Hand-off after a harvest, the acceptance runbook, one default database set (F15).

## Definition of done
- [ ] **0. Audit.** Observations 1 to 4 re-verified at `a0191cc6` (phase-auditor, adversarially checked). Lane declared.
- [ ] **1. A keyword query from the topic, without AI.** Derived deterministically from the topic sentence; the same rule at every front door (browser, CLI wizard, MCP); the topic sentence stays in the draft and protocol unchanged; the exact query each database received is shown; the researcher can edit it and search again. Tests: see Findings fixed (OBS-1).
- [ ] **2. "0 results" is said.** A database that returned nothing says "0 results", not "answered", in Explore and on the Harvest legs. Tests: see Findings fixed (OBS-1b).
- [ ] **3. A sample chosen by relevance.** The 25 are filled from each database's own order, spread across the selected databases in the researcher's order; deterministic; the representative of a duplicate group is unchanged (decision 2026-11-14, item 1). Test: four databases × 25 records give 25 with records from each, in the chosen order, identical on a second run (OBS-2).
- [ ] **4. arXiv combines terms.** Adjacent terms are joined with `AND`, as the arXiv API manual's Boolean syntax requires; Crossref is left as it is (no all-terms mode is documented). Test: OBS-3.
- [ ] **5. Databases selectable and re-orderable** in Explore and in Discovery (Plan and Harvest), keyboard-accessible and correct in right-to-left. Specs amended first (`02-explore`, `01-plan`, `03-harvest`). Component tests and a Playwright test for each screen.
- [ ] **6. Direction quality on a recorded pool** (OBS-4): a test on the recorded golden recon pool shows the relevance-chosen sample gives directions anchored in on-topic records; the direction code is not tuned.
- [ ] **7. Gates.** `/gate checkpoint` per item (golden cassette tests added by hand); `generate_contract_baseline.py --check` passes; `/gate pr` green on the final executable commit; `milestone-reviewer` APPROVE; Evidence filled. Stop before any push.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |

## Decisions
- [2026-11-14, Assisted inception](../../decisions.md) (accepted).
- [2026-11-14, M10a: where the database choice lives, the probe query, the arXiv cassette](../../decisions.md) (proposed; awaiting the researcher).

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| start | `a0191cc6` | branch `dev/m10a/search-quality` from `origin/main` | clean | |
| audit | `a0191cc6` | phase-auditor on OBS-1, OBS-2 (two adversarial verifiers each); readers on OBS-3, OBS-4, UI, storage, lane | OBS-1 to OBS-3 confirmed, none refuted; OBS-4 partly: a relevance sample improves evidence (9 → 18 DOI records, observed_in 2 → 3+) but the generic labels come from the direction scorer | |

## Deferred
