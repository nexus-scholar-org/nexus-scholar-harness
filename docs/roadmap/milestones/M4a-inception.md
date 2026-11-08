# M4a-inception: the inception engine pieces that do not collide with M3a
Branch: `dev/m4a/inception-engine` · Lane: **RELEASE, pending the researcher's confirmation** (the plan row for M4 is RELEASE. M4a changes CLI semantics, because re-inception now refuses without `--replace`, and it adds new HTTP routes. Both are RELEASE triggers in `test_gate_policy.md` §lanes) · Status: IN PROGRESS · Started: 2026-11-08

Why: plan §6 row "M4 Inception web" is split. M4a covers the engine work that touches neither `src/scholar_search/` nor `src/scholar_harness/recon/`, which M3a Discovery owns, nor the `scholar_protocol` models and compiler. Plan §1 has INC-08 and INC-22. Plan §2 "Phase 0 Inception" lists screens 00, 06 and 08 with their backend.

## Definition of done
- [ ] **INC-08. Re-inception refuses without `--replace`.** `run_wizard` refuses to write into a folder that already holds a workspace and writes nothing. With `--replace`, it backs up the old `protocol.json`, `intent.json` and `SCREENING_CRITERIA.md`, does not reset `project.json`, and records the replacement in the journal. Test: `tests/inception/test_inception_replace.py`.
- [ ] **INC-22. Every criterion is shown verbatim and accepted one by one.** The CLI wizard prints each inclusion and exclusion criterion with its source and asks for acceptance per item. A rejected criterion is not compiled. The MCP/agent path gets the same rule. Test: `tests/inception/test_inception_criteria.py`.
- [ ] **Stateless step API** over the existing wizard functions, with no second copy of wizard logic. The wizard and the API call the same helpers. Test: `tests/inception/test_inception_steps.py`.
- [ ] **Compile-preview** returns the protocol, its fingerprint, the screening-criteria text and the files that would be written, and writes nothing. Test: the same file, which asserts the tree is unchanged.
- [ ] **One gated genesis path** with the overwrite guard. The CLI wizard, `nexus-scholar init` and the HTTP route all write through it. Test: `test_inception_replace.py` and the HTTP tests.
- [ ] **Draft sessions with one session id** (screens 00 and 08; UX finding #10). Drafts are created, saved, listed, resumed and discarded over HTTP, and the wizard and MCP use one id format. Test: `tests/console/test_inception_api.py`.
- [ ] **Create a workspace from a draft** over HTTP through the gated genesis path. Test: `tests/console/test_inception_api.py`.
- [ ] **Gate:** `generate_contract_baseline.py --check` passes, plus the pr gate (and the closure gate if the lane is RELEASE).
- [ ] **Review:** the milestone-reviewer returns APPROVE.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |

## Decisions
<entries in docs/decisions.md made in this milestone>

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| start | `a273fc6` | `generate_contract_baseline.py --check` | Contract baseline current | |

## Deferred
- **Held until M3a merges** (decided by the session that split M4): INC-09 and INC-21, recon over HTTP (`recon/engine.py` uses the `scholar_search` providers M3a changes), and PROT-02, PROT-03 and PROT-08 (`scholar_protocol` models and compiler; PROT-03 is a contract change).
- **Method questions M1–M7** (`docs/ux/phase0-inception/README.md`) stay open, as plan §2 proposes.
- **All UI** (`apps/research-ui`), owned by the redesign session.
