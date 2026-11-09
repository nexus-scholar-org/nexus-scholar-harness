# M4b Inception screens over the step API
Branch: `dev/m4b/inception-ui` · Lane: **STANDARD** (UI over routes that M4a shipped and reviewed under RELEASE; the browser allowlist widens to those routes without changing their semantics, contract, identity or persistence; `test_gate_policy.md` §lanes. Escalate to RELEASE if the diff touches a route, a refusal code, the engine or the contract) · Status: IN PROGRESS · Started: 2026-11-09

Why: plan §6 row "M4 Inception web" lists UI for inception specs 00–08. M4a (PR #206) shipped the engine: drafts, the stateless step API, compile-preview and gated genesis (`docs/architecture/inception-api.md`). M4b builds the screens over it so a researcher creates a workspace from the browser without the CLI wizard. Recon over HTTP (INC-09/21) is still not built, so Explore and Direction stay placeholders.

## Definition of done
- [ ] **Specs.** `docs/ux/phase0-inception/final/01-scope.md`, `04-shape.md`, `05-criteria.md`, `06-review.md`, `07-done.md` and `08-states.md` are `Status: FINAL`. Each maps data in and out to the exact `/api/v1/inception` routes and refusal codes, and covers states, keyboard, en/fr/ar copy keys and acceptance tests. `02-explore.md` and `03-direction.md` are one-paragraph placeholders that wait for recon over HTTP. The researcher closes the open questions.
- [ ] **Browser surface.** `/api/v1/inception/*` GET, POST and PUT as the API defines them are added to `console/browser.py` and the Next proxy. Tests: `tests/console/test_browser_access.py` and `apps/research-ui/tests/console-proxy.test.ts`.
- [ ] **Screens.** The route group `/[locale]/inception/...` runs Scope → Shape → Criteria → Review → Done over the draft and step API.
  - Saves send `base_updated_at`, and the screen shows `DRAFT_CONFLICT`.
  - Each criterion appears verbatim with its source. A generated criterion defaults to "no".
  - Review previews with `POST /preview`.
  - Genesis has two confirmations: `WORKSPACE_EXISTS` leads to replace with a backup, and `SCREENING_BOUND` needs the slug typed.
  - After genesis, the screen opens the new workspace with `POST /workspaces/open` and lands on screening Home.
  - The flow starts from "New review" on the Workspaces screen.
- [ ] **Tests.** One vitest file per screen covers its states and shows refusals as sentences, with the code under Details. A Playwright spec runs against a stateful fake of the inception API. Axe checks pass in light and dark, and no page overflows at 375 or 1440 px.
- [ ] **Gate.** `/gate inner` after edits, then `/gate pr` once on the final commit.
- [ ] **Review.** The milestone-reviewer returns APPROVE.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |

## Decisions

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| start | `8726fb9` | branch from `origin/main` | clean | |

## Deferred
- **Explore (02) and Direction (03)** wait for recon over HTTP (INC-09/21). Drafts carry no grounded evidence.
- **Discarding a draft** (`DELETE /inception/drafts/{id}`): the browser surface carries GET, HEAD, POST and PUT only, and this milestone adds no method.
