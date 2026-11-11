# M4d-inception-bridge Grounded inception in the browser (Explore, Direction, synonyms, anchor seeds, replace semantics)
Branch: dev/m4d/inception-bridge · Lane: **RELEASE** (F1 moves researcher data under `literature/`, per [`three-phase-hardening-2026-11-10.md`](../../assessment/three-phase-hardening-2026-11-10.md) §4 item 2; the seeds add a draft field and write `search_strategy.golden_seeds`; `test_gate_policy.md` §lanes) · Status: IN PROGRESS · Started: 2026-11-11

Approved by the researcher in chat on 2026-11-11 (relayed by the coordinating session). Base: `origin/main` at `839a51dd`.

Why: the three-phase review (2026-11-10) found browser inception ungrounded. Explore and Direction were never built, so the compiled query has no synonyms (`"weed detection" AND "on-device inference"`); recon anchors never become `golden_seeds`, so discovery's Recall check has nothing to test; the probe ignores languages; the probe's behaviour without an OpenAlex key was unverified. M4d closes that seam with **no AI spend**. It covers most of the synonym and recall-repair value planned for M9d.

Out of scope (deferred by the researcher): tagging b7; the M9a cost measurement.

## Definition of done
Done in this order.
- [ ] **Step 0, F1 decision.** `phase-auditor` on F1 at HEAD; the researcher chooses the replace semantics; entry in `docs/decisions.md`.
- [ ] **1. Key and leg state on the recon probe.** Without an OpenAlex key, and with a Semantic Scholar key that is rejected (403) or throttled (429), the probe reports each provider's key and leg state instead of silently returning a thin pool; Explore shows that state as the Plan screen does. Offline tests with fakes or cassettes (socket guard on).
- [ ] **2. Years and languages reach the probe.** The draft's year window and languages are passed to the recon probe, are part of the pool and of its cache key, and are shown on Explore.
- [ ] **3. Explore and Direction screens** in `apps/research-ui` over the M4c recon routes, between Scope and Shape. Specs `docs/ux/phase0-inception/final/02-explore.md` and `03-direction.md` at `Status: FINAL` before the build. Explore shows pool size, provider legs and per-concept anchoring counts; on Direction nothing is applied without a click. en, fr, ar strings.
- [ ] **4. Synonyms from the pool, accepted one by one.** For each concept, the co-occurring pool terms with paper counts; each ticked term joins that concept's OR group in the compiled query. No language model.
- [ ] **5. Anchor seeds.** The anchored papers are offered as seeds; the ones kept are saved to the protocol's `search_strategy.golden_seeds` before acceptance or genesis; the discovery Recall screen then checks them.
- [ ] **6. F1 fix** as decided in Step 0, with its reproducing test written first.
- [ ] Gates: `/gate checkpoint` at the end of each item; PR gate once; contract baseline `--check` passes; `milestone-reviewer` APPROVE.

Optional tail, only if cheap and the researcher agrees: F6 (draft size limits), F5 (validation errors inside the refusal envelope), the three inception UI P3s (Criteria allows zero concepts; Review shows a refusal before the title is typed; Workspaces has two create buttons).

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |

## Decisions

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| start | `839a51dd` | branch `dev/m4d/inception-bridge` from `origin/main` | clean | |

## Deferred
