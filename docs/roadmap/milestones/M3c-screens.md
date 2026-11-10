# M3c-screens Discovery screens
Branch: `dev/m3c/discovery-screens` · Lane: **STANDARD** (packet §7: a UI over routes M3b-api and M3d-engine shipped; no engine or contract change; `generate_contract_baseline.py --check` at every commit) · Status: IN PROGRESS · Started: 2026-11-10

Why: plan §2 Phase 1 lists the discovery screens 01–08 and plan §6 M3 their specs. M3b-api (PR #214) and M3d-engine (PR #215) put the routes on `main` ([`DISCOVERY_API_PACKET.md`](../../architecture/research_ui/DISCOVERY_API_PACKET.md) §4, decisions §6, split §7). This milestone writes the eight specs against those routes and builds the screens, as M4b did for inception.

## Definition of done
- [ ] **Specs.** `docs/ux/phase1-discovery/final/01-plan.md` … `08-handoff.md` are `Status: FINAL` (04 an addendum to screening spec 11; 05 counts only). Each maps every field to a route and key in `console/api/discovery.py` or `console/api/screening_v1.py`, names every refusal code it can hit, and lists every board element without an engine under "Changed from the canvas". 01 holds the shared section (step bar, `?console=`, run selector, SSE rules, refusal copy). The researcher closed each spec's open questions.
- [ ] **Screens.** `apps/research-ui/app/[locale]/discovery/{,plan,recall,harvest,dedup,report,handoff}` with the step bar and run selector; Import hands over to the screening import screen with a return link; Discovery in the primary navigation between Inception and Screening. Components `components/discovery-*.tsx`, typed `lib/discovery-api.ts`, copy `lib/discovery-copy.ts` in en, fr, ar.
- [ ] **Tests.** Vitest per screen and the copy placeholder-parity test, over the stateful fake `tests/fixtures/discovery-engine.ts`; `tests-browser/discovery.spec.ts`: the full path Plan → Recall → Harvest (streamed) → Dedup → Report → Hand-off accept → screening Home; refusals `MAILTO_NOT_SET` (printed line), `CORPUS_ALREADY_ACCEPTED`, `DISCOVERY_JOB_ACTIVE`, a failed leg with its code, a capped leg as a lower bound, `PROTOCOL_CHANGED_SINCE_RUN` on accept; axe in en and ar, light and dark; overflow at 375 and 1440 px; a hydration test per screen with query parameters.
- [ ] **Gate.** `/gate inner` after edits, `/gate checkpoint` at the end of each half, `/gate pr` once on the final commit (full Python suite, contract check, vitest, build, Playwright), `milestone-reviewer` APPROVE.

## Decisions
- [2026-11-10, Discovery screens: ten answers that close specs 01–08](../../decisions.md) — the researcher took every recommended answer ("all recommended"); the specs became `Status: FINAL`. The drafts were written by two `ux-spec-writer` runs (01–04 with the shared section, 05–08) against the route facts verified at `b6643a0`.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| start | `b6643a0` | branch from `origin/main` | clean | |

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
