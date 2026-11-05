# 06 Agent proposals run    Status: FINAL | Phase 2 Screening | Route `/screening/proposals` | Milestone M1b (driver, routes, UI)

Board: `Proposals` (D3). Contract: `screening-api-contract.md` §4-§5; agent design `docs/architecture/agent-system.md` §2-§5.

**Purpose.** Decide whether and how the agent drafts proposals: choose the provider, see what leaves the machine and the cost, consent, run, and watch progress. Optional: check the agent on 30 of your labels first.

**Changed from the canvas.**
- **Providers:** Anthropic (default), an OpenAI-compatible endpoint (with its URL) and Gemini (decision 2026-11-05, M1b split). The driver is the engine calling the API with the researcher's key (`driver: "api"`); there is no local model. The key is set in the terminal (`nexus-scholar keys set <provider>`) and kept in the OS keychain; the screen shows only where it is stored (`GET /proposals/setup`).
- **Cost ceiling is a hard stop, set per run** (new field on the run gate; not on the canvas).
- Canvas "Pause run" becomes **Cancel** (the contract has `POST /proposals/runs/{run_id}/cancel`, no pause). A cancelled or partial run can be resumed by starting a new run over the records without a draft.
- **Ordering:** after a run, the queue can be ordered by the agent's uncertainty. That is a server-side queue view (03), disclosed in the methods paragraph, not a separate run.
- **Retention:** proposals are kept in the workspace permanently as append-only provenance; the screen says so.
- Canvas "Your Claude, through MCP" provider card is **not a driver option**. MCP starts no run through the API; the researcher's Claude calls `submit_proposal` over MCP. The screen shows it as an instruction ("run it from Claude", with `uv run scholar-agent`), not as a radio.
- The 30-label check is advisory (`POST /proposals/calibrations` ✗ M1b): a missed include shows a warning and never blocks a run.
- Output is machine output and is styled as a draft everywhere. This screen shows no proposal content.
- The run never excludes a record you have not seen; unproposed records stay in your queue.

## Entry / exit
- Entry: step bar "2 Agent proposals"; Home "Run settings"; after Prepare (02). The step is optional ("You can screen without any proposals at all").
- Exit: "Open triage while it runs" or run complete → 03. Gate: Run gate panel; nothing leaves the machine until Start, and `CONSENT_REQUIRED` refuses a run without recorded consent.

## Data in
| Field | Source |
| :-- | :-- |
| `{run_id, estimate{records, input_tokens, cost_usd}}` | response of `POST /proposals/runs` ✗ M1b (dry-run on one batch via the "Dry run" button) |
| `{state, done, failed, refused, truncated, cost_so_far}` | `GET /proposals/runs/{run_id}` ✗ M1b |
| `{task, providers[{provider, key, consent}], data_flow, active_run, latest_run}` | `GET /proposals/setup` (M1b-2) |
| settings | `GET /settings` ✗ M1a |
| previous runs, quarantined files | `GET /ui/audit-feed` ✓ `screening.py:1173`; `GET /ui/batches` ✓ `screening.py:572` |

## Data out
`POST /proposals/runs` ✗ M1b with `{driver:"api", model, effort, scope:{view|study_ids}, consent:{provider, accepted_at}}` (per-run cost ceiling: the run stops at `COST_CEILING_REACHED`, done proposals are kept). `POST /proposals/calibrations` ✗ M1b with `{study_ids, model, effort}` → `{run_id}`; result `{include_recall, ci_low, missed_includes[]}`. `POST /proposals/runs/{run_id}/cancel` ✗ M1b → `{state:"cancelled"}`. Journal: consent with provider, model and prompt hash; run start, completion or cancellation; rate-limit step-downs (D3 "journaled").

## Backend calls
| Call | Status |
| :-- | :-- |
| `POST /api/v1/screening/proposals/runs` | ✗ M1b |
| `GET /api/v1/screening/proposals/runs/{run_id}` | ✗ M1b |
| `POST /api/v1/screening/proposals/runs/{run_id}/cancel` | ✗ M1b |
| `POST /api/v1/screening/proposals/calibrations` | ✗ M1b |
| `GET /api/v1/screening/settings` | ✗ M1a |
| `GET /api/v1/screening/ui/audit-feed` | ✓ `screening.py:1173` |
| `GET /api/v1/screening/ui/batches` | ✓ `screening.py:572` |

## States
- **Default**: h1 "Which agent drafts the proposals, and what leaves this machine?"; Provider card (Anthropic, key stays in the engine, never written to the workspace or journal) with "What leaves this machine: titles and abstracts of every record in the run"; Run settings (model, prompt hash `sha256:…` with "Read the prompt", records and batches in parallel); Cost estimate in tokens (about 650 in and 60 out per record); consent checkbox; optional "Check the agent on 30 of your labels first"; Run gate with "Start agent proposals · n records" (brand) and "Dry run on one batch (20 records)".
- **Empty**: no batches → link to 02. No API key configured → "Set the key in the engine" with the instructions (the browser never takes the key). Nothing proposed yet → "While it runs" card shows state idle.
- **Loading**: skeleton for the estimate; during a run the "While it runs" card polls: "2,410 of 3,241 proposed · batch 121", bar, "4 at a time, down from 6 after a provider rate limit at 15:42 (journaled)", quarantined files "2 files quarantined with their reason · Open".
- **Error**: `CONSENT_REQUIRED`, `RUN_ALREADY_ACTIVE` (one run per workspace; also for calibrations), `COST_CEILING_REACHED` (contract §7), `PROVIDER_TRANSIENT` (✓ refusals.md; retry exhausted, attempt count shown), `RATE_LIMITED` (✓ `contracts/models.py:74`, shown as a step-down or partial stop), `INVALID_OUTPUT` (✓ refusals.md; the proposal failed validation, the record routes to Unclear and is not proposed), `QUOTE_NOT_IN_SOURCE` (✓ refusals.md; a validator result), `STALE_BINDING` (✓ `integrity.py:28`), `ENGINE_UNREACHABLE` (client-side).
- **Partial**: "The agent run stopped at 2,410 of 3,241 … 831 records have no draft. You can decide them without one." Button "Resume at 4 at a time" starts a run over the remainder. `truncated` and `refused` counts shown.
- **Offline**: provider unreachable → run shown as stalled with the attempt count; read-only; Cancel works once the engine answers.
- **Protocol-changed**: existing proposals marked stale ("bound to an older protocol") and not shown; a new run is required.

## Desktop layout
`Proposals` (D3): split. Main: Provider fieldset (two cards on the canvas), Run settings card, Calibration card. Side: "While it runs" card, Run gate. One brand button: Start. Proposals are drawn as `draft` surfaces wherever they appear.

## Mobile layout (≤ 640 px)
Not mounted on the LAN sub-app (contract §6). The phone sees no route here; Home shows the agent card read-only ("2,410 of 3,241 proposed").

## Keyboard
Tab order: provider, model, prompt link, consent, calibration, Dry run, Start, Cancel. `Enter` on Start opens a confirm dialog with the data-flow sentence and ceiling; `Esc` closes.

## Copy
`screening.proposals.title`, `screening.proposals.lede`, `screening.proposals.provider.*`, `screening.proposals.dataFlow`, `screening.proposals.cost.{estimate,ceiling,hardStop}`, `screening.proposals.consent`, `screening.proposals.promptHash`, `screening.proposals.run.{start,dryRun,cancel,resume,partial}`, `screening.proposals.retention` ("Proposals are kept in this workspace as provenance."), `screening.proposals.calibration.*`, `screening.refusal.CONSENT_REQUIRED`.

## Accessibility
Progress bar `role=img` with a sentence label; cost shown as text; state badges carry text. RTL: hashes in `bdi` LTR; numbers Latin.

## Acceptance tests
Vitest: `proposals.consent-required.test.tsx`, `proposals.cost-ceiling-hard-stop.test.tsx`, `proposals.no-content-before-decision.test.tsx`. Playwright: `screening/proposals.spec.ts` (dry run, consent, cancel, partial then resume).

## Decisions
1. Contract §9.6 (decided 2026-11-04): the estimate comes from a dated price table in the tasks folder, updated each release; the panel shows "prices as of <date>" beside the dollar figure.
