# M3c-screens Discovery screens
Branch: `dev/m3c/discovery-screens` · Lane: **STANDARD** (packet §7: a UI over routes M3b-api and M3d-engine shipped; no engine or contract change; `generate_contract_baseline.py --check` at every commit) · Status: READY FOR PR · Started: 2026-11-10

Why: plan §2 Phase 1 lists the discovery screens 01–08 and plan §6 M3 their specs. M3b-api (PR #214) and M3d-engine (PR #215) put the routes on `main` ([`DISCOVERY_API_PACKET.md`](../../architecture/research_ui/DISCOVERY_API_PACKET.md) §4, decisions §6, split §7). This milestone writes the eight specs against those routes and builds the screens, as M4b did for inception.

## Definition of done
- [x] **Specs.** `docs/ux/phase1-discovery/final/01-plan.md` … `08-handoff.md` are `Status: FINAL` (04 an addendum to screening spec 11; 05 counts only). Each maps every field to a route and key in `console/api/discovery.py` or `console/api/screening_v1.py`, names every refusal code it can hit, and lists every board element without an engine under "Changed from the canvas". 01 holds the shared section (step bar, `?console=`, run selector, SSE rules, refusal copy). The researcher closed each spec's open questions.
- [x] **Screens.** `apps/research-ui/app/[locale]/discovery/{,plan,recall,harvest,dedup,report,handoff}` with the step bar and run selector; Import hands over to the screening import screen with a return link; Discovery in the primary navigation (Workspaces · Discovery · Screening; Inception is not a navigation entry). Components `components/discovery-*.tsx`, typed `lib/discovery-api.ts`, copy `lib/discovery-copy.ts` in en, fr, ar.
- [x] **Tests.** Vitest per screen and the copy placeholder-parity test, over the stateful fake `tests/fixtures/discovery-engine.ts`; `tests-browser/discovery.spec.ts`: the full path Plan → Recall → Harvest (streamed) → Dedup → Report → Hand-off accept → screening Home; refusals `MAILTO_NOT_SET` (printed line), `CORPUS_ALREADY_ACCEPTED`, `DISCOVERY_JOB_ACTIVE`, a failed leg with its code, a capped leg as a lower bound, `PROTOCOL_CHANGED_SINCE_RUN` on accept; axe in en and ar, light and dark; overflow at 375 and 1440 px; a hydration test per screen with query parameters.
- [x] **Gate.** `/gate inner` after edits, `/gate checkpoint` at the end of each half, `/gate pr` once on the final commit (full Python suite, contract check, vitest, build, Playwright), `milestone-reviewer` APPROVE.

## Decisions
- [2026-11-10, Discovery screens: ten answers that close specs 01–08](../../decisions.md) — the researcher took every recommended answer ("all recommended"); the specs became `Status: FINAL`. The drafts were written by two `ux-spec-writer` runs (01–04 with the shared section, 05–08) against the route facts verified at `b6643a0`.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| start | `b6643a0` | branch from `origin/main` | clean | |
| checkpoint (half 1) | `7891141` | `generate_contract_baseline.py --check`; `git diff --check` (docs only) | pass; "Contract baseline current" | <10 s |
| inner | `caeb16a` | `npx tsc --noEmit`; `vitest run` shell, i18n catalog, keyboard, import, inception copy, harvest | clean; 71 + 6 passed | ~20 s |
| inner | `06acbbd` working tree | `npx playwright test tests-browser/discovery.spec.ts --project=chromium` | 56 passed, 2 failed (Harvest overflow at 375 px), fixed in `06acbbd` (`min-w-0` on grid columns) | 2.4 min |
| inner | `06acbbd` | `npx vitest run` (whole UI suite) | 423 passed, 1 failed (details rule: summaries without the focus ring), fixed in `06acbbd` | ~100 s |
| pr | `ce486ef` | `select_test_gate.py --changed main --stage pr` (typecheck, vitest, build, Playwright both projects) | typecheck, vitest 424 passed, build pass; Playwright 381 passed, 6 failed, 13 skipped: `screening-import.spec.ts:89`, `:117` (selector met the new limits field) and `shell.spec.ts:74` (keyboard ring without the Discovery link), each in light and dark; fixed in `5736767` | 10.0 min |
| review | `ce486ef` | `milestone-reviewer` | CHANGES: 3 P2 (engine message dropped for known codes, translated sentences forced left-to-right, recall count from form rows), 4 P3 (mailto Check again restarted a job, fake stage statuses, record gaps, 44 px card link); follow-up: accept during a running harvest | – |
| pr | `5736767` | `uv run pytest -q -n auto` (JUnit) | 4711 passed, 15 skipped, 0 failed | 439 s |
| pr | `5736767` | `generate_contract_baseline.py --check`; `git diff --check origin/main...HEAD`; `ruff check scripts/`; real-bug `ruff check src/` | all pass; "Contract baseline current" | <10 s |
| pr | `5736767` | `npm --prefix apps/research-ui run typecheck` / `test` / `build` / `test:browser` | clean; vitest 428 passed (37 files); build ok (74 pages); Playwright 387 passed, 13 skipped, 0 failed (light and dark). Screenshots restored, not committed | 7 s / 52 s / 31 s / 473 s |
| review | `5736767` | `milestone-reviewer` on the repair delta | **APPROVE**; one P3 follow-up (a test regex missing its backslash) repaired in the next commit | – |
| inner | next commit | `vitest run tests/discovery-recall.test.tsx`; `tsc --noEmit` (test-only repair of the regex) | 9 passed; clean. The `pr` evidence of `5736767` is reused for this test-file-only change and the record (policy "Evidence reuse") | ~10 s |

## Deferred
Route gaps found while writing the specs; each screen shows an honest state instead (see each spec's "Changed from the canvas"):
- **Anchor seeds on Recall** (packet §4.2): no route links an open workspace to its inception draft's recon binding. Needs an engine item that records the anchor papers (or draft id) in the workspace at genesis.
- **Protocol amendment from the browser** (packet §4.1, §4.2): no route opens an existing workspace's protocol as an inception draft; the screens link to the inception drafts screen.
- **Near-twin pair review** (packet §4.5 Stage 2, decision 2): M3e-neartwins, RELEASE lane.
- **Failed databases on the hand-off** (packet §4.8): `lower_bound_databases` names capped ones only; the hand-off links to the report (answer 10).
- **Hydration state** (packet §4.8): no route says whether abstracts were filled for the corpus (answer 9).
- **Report gaps** (packet §4.6): no total identified across databases, `cache` always `null`, no dedup counts for an older run, `not_searched` has two reasons only.
- **Harvest gaps** (packet §4.3): no per-database stop, retry or split, no slice yield, no running total while a run is in progress, no cancel reason.
- **Plan gaps** (packet §4.1): no reported totals before a run (the board's dry-run counts).
- **Works count on the hand-off for a harvest** (packet §4.8, found while building): `corpus.preview` counts staged exports only (zero for a harvest) and `GET /discovery/handoff` has no field for the number of works a harvest hands to screening. The headline carries no number; a `works` field in the hand-off answer is a small engine follow-up.
- **Screen simplifications** are listed under each spec's "As built (M3c)": no step marks outside the entry page, no skeletons, no "As of" caption while the engine is unreachable, fetch-streamed events instead of `EventSource`, no phone-specific pointer card.
- **Fake fixture**: the `recall` option of `tests/fixtures/discovery-engine.ts` is declared but seeds no stored check; the tests run a real check through the fake instead.
- **Engine guard on the accept during a harvest** (reviewer follow-up, packet §4.8): `POST /screening/corpus/accept` does not check the discovery job manager, so an accept from another client can freeze the previous run's `verified.json` while a new harvest runs. The hand-off screen disables Accept while `active_job.kind == "run"`; the engine should refuse `DISCOVERY_JOB_ACTIVE` itself.
- **Recall under a capped database** (reviewer follow-up, packet §4.2): a `not_found` under a capped leg may only mean the paper lies beyond the cap; the copy does not say so and the engine does not mark it.
- **Import screen reads `?console=` during render** (`components/screening-import.tsx`, older than M3c; reviewer note): the same hydration risk the discovery screens avoid.
