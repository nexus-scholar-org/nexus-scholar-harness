# Production plan: Inception, Discovery, Screening

**Status:** DECISIONS CONFIRMED 2026-11-03: option C staged from A0, MCP-first plus BYO key, the brand book as the design system (recorded in [`decisions.md`](../decisions.md)). **Revised the same day after an independent review:**
- the screening wedge ships at week 6;
- Discovery is stretch;
- the web Inception wizard moves past the horizon;
- you see every record by default;
- Unclear is stored as MAYBE.

The revised sequence is in §6. Implementation has not started; M0 waits for go-ahead.
**Base:** `main` at `4229f04`. The contract baseline check passes there (`generate_contract_baseline.py --check`: "Contract baseline current").
**Scope:** Phase 0 Inception, Phase 1 Discovery and Phase 2 Screening, each end to end (backend and UI). Everything else is frozen and labelled "not production" (§8).
**First paying user:** solo PhD researchers, then labs and institutions. **Horizon:** 1 month for the screening wedge, 2 months for all three phases. **Infra and token budget:** to be decided. The recommended architecture needs none in stage 1 (§5).

Evidence labels: **V** means re-read at `4229f04` during this planning pass, by one of four read-only audits (Inception, Discovery, Screening, Deployment) or by me. **I** means inferred and still to be confirmed by a reproducing test. Assessment IDs refer to [`docs/assessment/`](../assessment/README.md).

---

## 1. Current-state audit

### 1.1 What already exists

| Layer | Inception | Discovery | Screening |
| :-- | :-- | :-- | :-- |
| Wireframes | 11 canvas boards, six-step flow, States board (`docs/ux/phase0-inception/wireframes/`). Designed for **CLI and chat only, with no web front end**. | 8 boards: Main, Plan, Recall, Harvest, Report, Dedup, States, Handoff (`phase1-discovery/README.md:24-33`). Framed as a CLI redesign. | 8 desktop boards at 1200 px: Main, Prepare, Calibrate, Progress, Triage, Agreement, States, Publish (`phase2-screening/README.md:26-35`). **No mobile, empty, loading or offline states.** |
| Brand key-screens | Review and emit (`key-screens/Review.dc.html`) | none | Triage, light and dark (`key-screens/Main.dc.html`) |
| research-ui | none | none (overview counts are mocks, `lib/mock-project-states.ts:34`) | `/[locale]/screening`, `components/screening-page.tsx` (951 lines). Mock by default; `?source=live` loads **only the first batch** (`:754-761`). Include/Exclude only, one save per row, no keyboard, swipe or offline. AI recommendations are not shown. |
| Backend reachable from UI | none: no inception, recon or protocol endpoints in `console/api/*.py` | `GET /literature/candidates`, `GET /harvest/corpus` (`console/api/workspace.py:128,243`). The `discovery` and `dedup` job actions are broken (`console/runtimes/actions.py:52-64`). | Batches, rows, review, criterion-refs, audit-feed, draft decisions POST, pairing/defer/publish, publication outputs (`console/api/screening.py:102-1582`, `workspace.py:690`) |

Transport today (V): the browser calls `app/api/console/[...path]/route.ts`, a same-origin proxy that forwards to the FastAPI console. The console is started with `nexus-scholar serve`, listens on `127.0.0.1:8765`, and serves **one existing workspace per process** (`cli.py:1012-1041`, `console/serve.py:31-73`). Nothing in Node spawns Python. Next builds with `output: "standalone"` (`next.config.ts:28`). There is no auth anywhere.

### 1.2 In-scope assessment findings (all re-verified as still present unless marked)

**Screening, Phase 2**

| ID | Defect at HEAD (V) | Fix | Effort |
| :-- | :-- | :-- | :-- |
| CON-10 | `collector.py:335-338`: dual mode only starts when an adjudication file exists, so screener 2 is ignored | Enter dual mode on any `*_screener2.json`; refuse unadjudicated disagreement | S |
| CON-14 (+CON-15) | `collector.py:536-558`: MAYBE/MAYBE becomes a COMPOSED consensus; the dual path never calls `check_no_unresolved_for_finalize` (called only at `:786,:893`). The dual artifact id comes from `batch_id` alone (`:628-635`). | Run the unresolved, coverage and duplicate gates on the dual path; derive the id from decision ids | S |
| CON-11 | Missing decision becomes INCLUDE (`collector.py:851`), confidence 0.80 (`:870`), method `LLM` (`:922`), 1970 timestamps (`:919`; `batcher.py:174-180`). The console writer stamps no `method`, `screener_id` or `decided_at` per row (`console/api/screening.py:63-78`). The UI sends `reviewed_by:"researcher-draft"` (`screening-page.tsx:221`). | Refuse missing provenance; the writer stamps `method:HUMAN`, the screener and `decided_at` on every row | S |
| CON-13 | `contracts/acceptance.py:433` and `contracts/chain.py:250` only check single-parent artifacts | Require exactly one `screening_batch` parent | S |
| CON-02/03 | Approver identity is read from the agent-writable `operator_context.json` (`authority/review.py:154-197`). One override approves every batch (`:877`, `:658-672`). | Per-batch verified approval. Relabel the approver as an unauthenticated local attestation until real auth exists. | M |
| AGT-16/18/19 | MCP `nexus_screen*` writes final `included/excluded/prisma` directly (`scholar_agent/server.py:429-480,554-575`). κ = 1.0 with one rater (`scholar_search/screening.py:743-751`). No MCP tool writes to the journal. | MCP writes **proposals only**; κ refuses fewer than 2 raters; state-changing tools append journal rows | M |
| SRCH-16/17/35 | Missing becomes INCLUDE, non-INCLUDE becomes EXCLUDE (`screening.py:550-553`); a missing vote counts as EXCLUDE (`:822`); `ScreeningDecision` has no method/model/prompt fields (`:17-28`) | Route uncertainty to the human; never impute votes; record method, model and prompt hash | S–M |
| UI-proxy (new) | The proxy allowlist accepts `actions/redeem` but client and console use `actions/pairing/redeem` (`route.ts:41-44` vs `lib/screening-api.ts:714`). I: approval cannot complete from the UI. The test asserts the wrong path (`tests/console-proxy.test.ts:227-238`). | Fix the path and the test | XS |

**Discovery, Phase 1** (none fixed)

| ID | Defect at HEAD (V) | Fix | Effort | Contract? |
| :-- | :-- | :-- | :-- | :-- |
| SRCH-30, CORE-21 | The executed per-provider query, hit totals, caps and dates are never recorded (`crossref.py:84`, `pubmed.py:138`, `engine.py:43-63`). The journal carries aggregates only (`pipeline/discovery.py:493-515`). Raw files are overwritten (`:413-414`). | `search_all` returns a `SearchLeg` per provider; journal the legs; run-numbered raw files | M | No (not a v1 type) |
| SRCH-11, SRCH-31 | One page per provider (`crossref.py:86-103`, `arxiv.py:196-225`, `pubmed.py:144-158`). The pool size is used as a retrieval cap, default 100 (`protocol_adapter.py:73-74`). | Paginate, read totals, emit `cap_hit`, no cap by default | M | SRCH-31: `target_candidate_pool_size` semantics are a protocol decision |
| SRCH-12/13/14 | arXiv silent compaction (`arxiv.py:150-194`); bioRxiv drops operators, including NOT, and is in the default set (`biorxiv.py:24-27`, `engine.py:30-37`); PubMed regex rewrite (`pubmed.py:138`) | Report the executed string; drop bioRxiv from the defaults; translate from parsed tokens | S each | No |
| SRCH-10 | A DOI resolving returns "verified" with no title check (`verifier.py:65-90`) | `DOI_TITLE_MISMATCH` status; never swap records | S | No |
| CORE-06, CORE-10 | Arrival-order `SCI-` ids are renumbered every run (`dedup.py:109-112`, `pipeline/coordinator.py:444-446`). The DOI bridge can merge two studies (`pipeline/verification.py:116-120`). | Sort before dedup; join on snapshot ids; stop re-running discovery on resume; quarantine claimed ids | M + S | Indirect (COMPASS input-order invariance) |
| CORE-07 | `cmd_prepare` exits on a missing registry (`batcher.py:198-200`) because **no runtime code calls `build_corpus_snapshot_artifact`** (`scholar_search/identity.py:296-398`) | This is **WP-01 Packet B adoption**; catch the exit and journal `PIPELINE_RUN_ABORTED` | M | Yes (Packet B) |

**PDF-07/08 are out of scope.** They belong to the full-text stage, after the collect gate (`console/runtimes/actions.py:81-86`, `pipeline/coordinator.py:456-466`). They are parked with full-text.

**Inception, Phase 0**

| ID | Defect at HEAD (V) | Fix | Effort | Contract? |
| :-- | :-- | :-- | :-- | :-- |
| INC-01 | The console has no auth or Host check (`console/serve.py:30-73`). The CORS comment "browsers never mutate" (`:58`) is false. Pipelines and jobs run arbitrary `uv run` commands (`api/pipelines.py:460`, `pipeline_executor.py:199`). The UI proxy strips Origin (`route.ts:160-176`). | Per-launch bearer token, TrustedHost, command allowlist, Origin check in the proxy | M | No |
| INC-08 | `run_wizard` overwrites an existing protocol (`wizard.py:363-368`; guard only in `init_command:434`) | Guard plus `--replace` with a backup | S | Indirect |
| INC-22 | Criteria are injected without being shown (`intent.py:236,250`; the confirm panel shows counts only, `wizard.py:349`) | Show every criterion verbatim and accept it per item | S | Compiled content changes |
| INC-09, INC-21 | Empty or failed pools are cached forever (`recon/engine.py:290-310`); "anchored" accepts any DOI in the pool (`grounded.py:417-453`) | No caching of failures plus `refresh`; require a term occurrence | S each | No |
| PROT-02, PROT-03 | Compile skips cross-field checks (`scholar_protocol/compiler.py:240`); unknown keys are dropped silently (`models.py:86-303`, no `extra="forbid"`) | Validate in compile; forbid extras | S each | **PROT-03: yes**, needs an architecture decision plus golden fixtures |
| PROT-01, PROT-08 | Trust and verification fields are never enforced (only rendered, `render.py:76-87`); the renderer omits date range, languages and two-tier screening | PROT-01: relabel as advisory (Phase 4 is parked). PROT-08: render the fields and version the renderer. | S | PROT-08 enters the screening binding |
| AGT-01, CORE-17 | MCP paths escape the workspace (`scholar_agent/server.py:207-216`). API keys are written into `.mcp.json` files that are not gitignored (`mcp_setup.py:33-104`; `git check-ignore` rc=1). | Contain paths; use env-var references; gitignore the files | M + S | No |
| AGT-07 | **Fixed** in `0a0bcfc` (`server.py:309-310`) | — | — | — |

### 1.3 Structural gaps that shape the plan

1. **Screening cannot be reached from a fresh run** until Packet B is adopted (CORE-07). Screening hardening can still land first, against a fixture workspace whose snapshot is built in a fixture script, as the tests already do. The real golden run needs Packet B.
2. **The decision store is not mergeable.** The batch file is last-writer-wins with no per-row timestamp (`console/api/screening.py:174-223`). Decision ids hash `decided_at` and change on every save (`collector.py:929-942`). Batch membership is positional and `prepare(force=True)` can reshuffle it (`batcher.py:257-268`, `coordinator.py:444-446`). Approval digests break on any edit (`review.py:880-903`). An offline phone queue needs per-record decision events keyed by `STU-` id (§4).
3. **AI proposals and human decisions share one file** (`batcher.py:136`), and the only worker writes `PENDING_REVIEW` with no reasons (`worker.py:266-275`). The wedge requires them to be separated.
4. **The LLM path is Gemini-only** (`scholar_search/screening.py:591-621`). No Anthropic provider exists in `src/`. Claude is reachable only through MCP and the file handoff.
5. **Inception has no web front end and no stateless step API.** The wizard runs only through the interactive `Responder` protocol (`wizard.py:40-70`). The console needs a workspace to exist before it starts (`cli.py:1029`), but inception is what creates the workspace.
6. **No offline-reproducible search.** The hishel cache ignores its config (`http_client.py:70-78`); the VCR cassette directories are empty. Correction after review: `workspaces/uav-crop-weed-v03/calibration_v03/` does hold raw files for five providers (`v03_20261017_raw_*.json`). The first audit only looked in `literature/`. That workspace's 570 screening files are also the source for the prompt-gate eval (agent-system §5).
7. **An RIS importer exists** (`scholar_search/importers.py:11`, CLI `import` at `scholar_search/cli.py:455`). Whether the harness discovery stage can take imported records as a source is **unverified**. If it can, a researcher can bring a Scopus/WoS export straight to screening.

---

## 2. Wireframes → final specs

**Format.** `docs/ux/<phase>/final/NN-<screen>.md`, one page per screen, from a shared template (`docs/ux/final-spec-template.md`):

```
# NN Screen name           Status: FINAL | Phase | Route | Milestone
Purpose            one sentence: the researcher's job on this screen
Entry / exit       where from, where to, what gate
Data in            fields, source endpoint, contract type
Data out           writes, endpoint, journal event emitted
Backend calls      method + path (existing ✓ / new ✗ + milestone)
States             default · empty · loading (skeleton) · error (typed refusal → copy) · partial · offline · stale/protocol-changed
Desktop layout     reference to the brand key-screen or a new board
Mobile layout      ≤ 640 px layout, touch targets ≥ 44 px, gestures
Keyboard           shortcuts, focus order
Copy               i18n keys (en master; fr/ar per §8 cuts)
Accessibility      contrast pair, RTL notes, screen-reader labels
Acceptance tests   vitest / Playwright spec names
Open questions     must be empty to mark FINAL
```

The canvas boards stay as design history. Final specs cite them; they are not redrawn.

### Phase 2 Screening (specs first)

| # | Screen | Source board | Main new backend |
| :-- | :-- | :-- | :-- |
| 01 | Screening home: batches, progress, lane status | Progress | cross-batch summary |
| 02 | Prepare and binding check | Prepare | prepare-from-UI job (allowlisted) |
| 03 | Triage queue, desktop: queue then detail, AI proposal beside the human decision, keys I/E/U/S/Z(undo) | Triage + key-screen Main | queue across batches; per-record decision event; proposal read |
| 04 | Triage, mobile: one card, swipe right Include / left Exclude / up Unclear, reason sheet, undo toast, offline badge | new | same as 03 plus the sync endpoint |
| 05 | Record detail: abstract, criterion refs, evidence quotes, proposal rationale | Triage | criterion-refs ✓ |
| 06 | AI proposals run: provider, model, prompt hash, cost estimate, consent | new | proposal job |
| 07 | AI concordance: descriptive AI-vs-human agreement, **not** κ (one human is not inter-rater). True κ appears only with two human screeners. | Agreement | concordance read |
| 08 | States: protocol changed, missing field, title only, failed shard, unresolved, not approved | States | typed refusals ✓ |
| 09 | Publish: PRISMA preview, per-batch approval, pairing on phone (QR) | Publish | PRISMA preview; pairing begin |
| — | Calibrate (30 self-labelled records) | Calibrate | **cut candidate** (§7); CON-17 says the CLI crashes |

Open UX questions to close in 01–09:
- Four outcomes against three swipe directions. Proposal: Skip is a button, not a swipe.
- Reason capture on a phone. Proposal: one tap from protocol exclusion codes; free text optional.
- Undo window, and whether undo is an event or a deletion. Proposal: undo is a new superseding event, never a delete.
- **Decided — blinding:** the agent proposal is hidden until you decide (default; a workspace setting recorded in provenance). Queue filters that reveal how the agent split ("agent disagrees") are post-decision views only.
- **Decided — you see every record by default.** The agent orders the queue and proposes; it never excludes a record you have not seen. AI-agreed exclusion is an explicit opt-in with a sample audit, and the methods paragraph states it (PRISMA 2020 item 8).
- **Decided — Unclear is stored as the existing `MAYBE`** of `ScreeningDecisionValue` (`contracts/models.py:93`) and labelled "Unclear → full text" in the UI and provenance. No contract version bump; the collector's refusal of MAYBE at finalize changes in M1a.
- How a pairing code reaches a phone. Proposal: a QR on the desktop screen.

### Phase 1 Discovery

| # | Screen | Board | Main new backend |
| :-- | :-- | :-- | :-- |
| 01 | Search plan: query per database, executed translation, limits (dry run) | Plan | plan dry-run |
| 02 | Recall check against inception anchor papers | Recall | `validate-query --seed` over HTTP |
| 03 | Harvest, live: per database fetched vs reported total, cap flags | Harvest | protocol-bound discovery job + per-leg SSE |
| 04 | Import: RIS/CSV from Scopus/WoS/other, with database name and date | new | import job (§1.3-7) |
| 05 | Dedup review: tiers, near-twin pairs, merge/split decision | Dedup | dedup summary + decision write + journal (D6) |
| 06 | Search report: PRISMA-S identification per database, methods text, run history | Report | legs read |
| 07 | States: failed, empty, cap reached, protocol changed, no contact email | States | — |
| 08 | Hand-off to screening: corpus snapshot accepted | Handoff | snapshot acceptance (Packet B) |

Open: whether the cap moves into a protocol field (README:58-59, a protocol decision); Scopus/WoS coverage through import (D11); polite-pool `mailto` default `student@university.edu` (`config.py:13`) must become a required setting.

### Phase 0 Inception (web front end is new)

| # | Screen | Board | Main new backend |
| :-- | :-- | :-- | :-- |
| 00 | Workspace picker / create | new | multi-workspace server, create endpoint |
| 01–05 | Scope, Explore, Direction, Shape, Concepts & criteria | StepScope…StepCriteria | stateless step API over the wizard functions; recon probe/distill/delta over HTTP |
| 06 | Review and emit: the only write gate; every criterion verbatim (INC-22) | Review + key-screen Review | compile-preview without writing; gated genesis with overwrite guard |
| 07 | Done and hand-off | StepDone | — |
| 08 | States and resume draft | States | draft session persistence, unified session id (UX #10) |

Open: M1–M7 method questions (`phase0-inception/README.md:39-72`). Two of them, M4 (provider, date and mode in the protocol) and M6 (PICO/SPIDER), are contract decisions. **I propose to leave all seven open** and label them visibly, rather than solving them in a two-month window.

---

## 3. Theme

**Conflict to resolve first.** `apps/research-ui/docs/VISUAL_DIRECTION.md` is the UI's design system of record (UI README:70-74). It contradicts `docs/ux/brand/BRAND_BOOK.md` on ground colour, web fonts, mono role, radius (0 vs 4/6/10), containers, focus colour, status names and dark mode (VD:232,270-277,345-348 vs BRAND_BOOK:47-108). `globals.css` uses none of the brand tokens (`@theme` at `:134-171`).

**Proposal: the brand book wins.** It is newer, it designs both themes, and its status roles match screening outcomes. The parts of VISUAL_DIRECTION that don't conflict, such as "rules, not containers" for dense tables, are kept as amendments. One `docs/decisions.md` entry records the reversal of VD decision D1. `GATES.md` §1.2/§3.7 and the colour checks in `tests-browser/focus-visibility.spec.ts` and `hygiene.spec.ts` are updated in the same PR.

**Pipeline.**
1. `docs/ux/brand/tokens.json` stays the single source.
2. A small generator (`apps/research-ui/scripts/build-tokens.mjs`, run in `prebuild` and checked in CI with `--check`, mirroring the contract-baseline pattern) emits `app/theme.css`:
   - `@theme` with `--color-*`, `--font-*`, `--text-*`, `--spacing-*` and `--radius-*` mapped to Tailwind 4 utilities;
   - `:root` holds the light values. Dark values are set under `@media (prefers-color-scheme: dark)`, applied only when the user hasn't picked a theme, and under `[data-theme="dark"]` for the manual toggle.
3. **Fonts:** BRAND_BOOK:77 says Google Fonts. Replace that with **self-hosted** Literata, Public Sans and IBM Plex Mono through `next/font/local`, because a local-first, privacy-sensitive tool must not call Google on every page load, and must work offline.
4. **Density:** add `density.comfortable|compact` tokens (row height, cell padding). Triage on desktop defaults to compact; mobile is always comfortable (44 px targets, BRAND_BOOK:106).
5. **Status naming:**
   - decision outcomes use the brand's `include / unclear / blocked / exclude`;
   - system states keep the UI's `success / warning / refusal`, re-pointed at the brand colours;
   - `anchor` is reserved for provenance (BRAND_BOOK:49).

**Components.**
- **Build from the brand previews:** `StatusBadge` (replaces `components/status-badge.tsx`), `GatePanel`, `EvidenceQuote`, `DataCell`.
- **New:** `Button` (one brand action per screen), `DecisionBar`, `RecordCard` (swipeable), `QueueList`, `ProgressMeter`, `ProposalPanel` (styled as a draft, BRAND_BOOK:21), `EmptyState`, `ErrorState` (typed refusal → copy), `Skeleton`, `UndoToast`, `OfflineBadge`, `QrPairing`, `ThemeToggle`.
- **Restyle:** `app-shell`, `primary-nav`, `mobile-nav`, `pairing-dialog`, `locale-switcher`.
- **Not built:** `TrustLevel` (RoB-trust is parked).

---

## 4. Mobile

**All screens:** responsive first, at breakpoints of 640 / 1024 px. Every final spec has a mobile layout. RTL (ar) is checked in Playwright at the mobile width. Today Playwright runs chromium only; add WebKit mobile emulation for the screening specs.

**Screening on a phone: the one flow that must be excellent.**
- **Input:**
  - swipe right Include, left Exclude, up Unclear; Skip is a button;
  - a haptic-free visual commit at 40 % travel, with a 5 s undo toast;
  - on desktop, keys I / E / U / S / Z;
  - an Exclude reason is required: one tap from the protocol's exclusion codes.
- **Decision model (backend, milestone M1):** each tap becomes a `ScreeningDecisionEvent` with these fields:
  - `event_id` (a client UUIDv7) and `study_id` (`STU-`, order-independent, `identity.py:320-331`);
  - `screener_id`, `method: HUMAN`, `decided_at` (client clock plus server receipt time);
  - `outcome`, `reason_code` and `supersedes`;
  - `proposal_ref`, the hash of the AI proposal shown, if any;
  - `protocol_fingerprint` and `batch_binding` digests.

  Events append to a per-screener JSONL. The batch decisions file becomes a **projection** of those events, so the existing collector and acceptance path keep working. Replays are idempotent by `event_id`. A conflict, meaning two non-superseding events for one study and one screener, is surfaced for the researcher to resolve, never auto-resolved. A replay after approval invalidates that batch's approval visibly. This keeps per-batch approval (CON-03) intact.
- **Offline queue:**
  - IndexedDB queue in the page, flushed on reconnect with exponential backoff.
  - IndexedDB works without a secure context, so on a LAN connection a queue survives a dropped connection, but **not a reload while offline**.
  - Reloading while offline needs a service worker, which needs HTTPS. That comes with the sync tier, or with an opt-in `mkcert` setup (§5).
  - The badge always shows how many decisions are queued.
- **How the phone reaches the engine (stage 1):** `nexus-scholar ui --lan` serves a **restricted sub-app** on the LAN: screening reads and decision events only. The jobs, pipelines and streams routers that run commands are never mounted there, because a photographed QR code or a LAN sniffer must not gain command execution. Phone tokens are short-lived and separate from the desktop's per-launch token (the INC-01 fix is a hard prerequisite). The desktop shows a QR code with the URL plus a one-time pairing token; the phone exchanges it for a session cookie, and nothing goes in URLs after first load.
- **Native apps, later:** a client for the same `/api/v1` contract, an offline store of events, push for "new batch ready", store accounts, and a sync backend. They are only worth building after sync exists and users ask for them.

---

## 5. Deployment architecture (decision needed from you)

### 5.1 Facts that change the cost picture (V)
- A FastAPI server already exists (`console/serve.py:36`, routers under `/api/v1`), and fastapi and uvicorn are base dependencies (`pyproject.toml:43,59`).
- The UI already talks to Python only over HTTP.
- The UI already prerenders `en/fr/ar` (`app/[locale]/layout.tsx:60`), so a static export is close. The route-handler proxy and the `/`→`/en` redirect move into FastAPI.
- The license is MIT, version 1.0.0 (`pyproject.toml:11`).

### 5.2 Options

| | **A0** `uv tool install` + `nexus-scholar ui` | **A** Desktop (Tauri + Python sidecar) | **B** Hosted web first | **C** Hybrid: local engine + optional account |
| :-- | :-- | :-- | :-- | :-- |
| Workspace | local folder (unchanged format) | local folder | server DB, so the format diverges | local folder canonical; optional encrypted sync copy |
| AI wiring / who pays | user's own Claude Code / Claude Desktop through MCP (their subscription), or BYO Anthropic/Gemini key | same; key in the OS keychain | hosted proxy; **you** pay and resell tokens | BYO or MCP by default; hosted tokens as an add-on |
| Privacy of unpublished reviews | best: only LLM calls leave, with per-provider disclosure | best | worst | good if sync is end-to-end encrypted |
| Paid tier can gate | support/onboarding only | signed installers, support | seats, tokens | sync, team dual screening with real κ, institutional SSO, hosted tokens, support |
| Auth | per-launch local token | same | full accounts, multitenancy | local token + account only for sync |
| Update channel | PyPI (`uv tool upgrade`) | Tauri updater from GitHub Releases (signing key loss bricks updates) | continuous deploy | PyPI/desktop + service |
| Signing cost | none | Apple $99/yr; Windows Azure Trusted Signing ~$10/mo (eligibility from Algeria **unverified**) | none | as A, if desktop |
| Maintainer cost of 3 clients | one UI, one server | + freezing Python per OS, sidecar lifecycle | + ops, GDPR, on-call | medium now; sync conflict semantics later |
| Phone | LAN + QR (§4) | same | native fit | sync → PWA |
| Fits the wedge | yes | yes | contradicts it | yes |

Sources: [Tauri sidecar](https://v2.tauri.app/develop/sidecar), [Tauri updater](https://v2.tauri.app/plugin/updater/), [Azure Artifact Signing pricing](https://azure.microsoft.com/pricing/details/artifact-signing/), [Next static exports](https://nextjs.org/docs/app/guides/static-exports), [Claude Desktop Extensions](https://www.anthropic.com/engineering/desktop-extensions).

### 5.3 Recommendation: C, staged, starting at A0

- **Stage 1 (this plan, months 1–2): A0 + MCP.**
  - `nexus-scholar ui [--workspace|--root] [--lan]` serves the static-exported UI and `/api/v1` from the one FastAPI process, same origin, behind a per-launch token, and opens the browser. `next dev` with the proxy stays for development only.
  - The agent experience is Claude Code / Claude Desktop through `scholar-agent`, shipped as an `.mcpb` Desktop Extension plus `nexus-scholar setup-mcp`, reworked to put no keys in files (CORE-17). The agent works inside the workspace and writes **proposals**; the researcher decides in the UI. The user's subscription pays for tokens.
  - BYO Anthropic key (new provider next to Gemini) for in-app proposal runs.
  - **No hosted infra.** Cost to you: PyPI and GitHub only. Tokens are needed only for the golden runs, cents for 30 records.
  - **Paid in stage 1:** nothing is gated in code. Offer a paid "founding lab" onboarding and support package, plus a waitlist for sync/team. That validates willingness to pay before building billing.
- **Stage 2 (after ~10–20 real users), whichever they ask for first:**
  - Tauri desktop with a PyInstaller sidecar and signed installers, if install friction is the top complaint;
  - or **sync + team screening** as the first coded paid feature: end-to-end encrypted replication of the append-only decision/journal events (§4 makes this a merge of event logs, not files), a second human screener with real κ, then SSO and audit export for institutions.
- **Stage 3:** installable PWA with full offline on top of sync; native mobile only if usage data justifies it.
- **Licensing:** keep MIT for the engine, UI and MCP server (already published under MIT). Sync, team service, hosted proxy and SSO go in a separate proprietary repo. Adopt DCO sign-off now to keep options open.
- **Not recommended: B.** It contradicts the privacy wedge, makes token resale a margin and abuse risk, and adds operations one maintainer cannot carry.

The decision entry for `docs/decisions.md` is written **after** you confirm (§9).

---

## 6. Sequencing

One PR per milestone, from `main`, through the fork. Lane declared up front; the owning full suite runs once per PR candidate; `generate_contract_baseline.py --check` runs in every PR. A milestone's backend and UI ship together.

**Revised 2026-11-03 after an independent review** (verdict: sound with changes), with the researcher's agreement. The screening wedge ships at week 6 (M5-slim). Discovery (M3) is stretch. The web Inception wizard (M4) moves past the horizon; inception stays CLI/MCP, labelled beta. Two review findings drove the change:
- screening could not be reached before week 6, because nothing builds a corpus snapshot outside tests (§1.3-1);
- M1 was too large for one person in two weeks.

| M | Weeks | Content | DoD | Lane |
| :-- | :-- | :-- | :-- | :-- |
| **M0 Foundations** | 1 | INC-01 (token, TrustedHost, allowlist, proxy Origin); fix the redeem path; CORE-17; AGT-01; brand tokens → `theme.css` generator + dark mode + self-hosted fonts + base components; final-spec template; golden workspace scaffold `workspaces/golden-uav-30/` with its protocol; `scripts/check_golden_workspace.py` (journal covers every stage; every decision has HUMAN provenance; PRISMA counts reconcile). **Added:** (a) a minimal **`nexus-scholar accept-corpus`** that calls `build_corpus_snapshot_artifact` (`scholar_search/identity.py:296`) on `literature/verified.json` or a RIS/CSV import, registers it, and runs the baseline drift check; this is the screening entry path. (b) The Unclear storage decision: existing `MAYBE` (§2). (c) The `--lan` threat model written into the INC-01 DoD (§4). | Each security finding has a failing-then-passing test; `accept-corpus` lets `prepare` succeed on a fresh workspace (test); existing Playwright suite green on the new theme in light and dark | STANDARD (`accept-corpus` touches Packet B; escalate to RELEASE if it changes snapshot semantics) |
| **M1a Screening backend** | 2–3 | CON-10/11/13/14/15, CON-02/03 (per-batch approval, approver relabelled as an attestation), SRCH-16/17/35, AGT-16/18/19; collector accepts `MAYBE` at finalize as "Unclear → full text"; **decision events** keyed by client `event_id` (UUIDv7), with `decision_id` derived from `event_id`, not from `decided_at`; a projection that excludes conflicted studies so the coverage gate refuses collect visibly; proposal store, validators and journal events (agent-system §2–§4); MCP read tools and `submit_proposal`; endpoints: cross-batch queue, decision-event POST, proposal read, PRISMA preview, pairing begin. | Reproducing test per P0; **replaying the same event set gives byte-identical output and keeps approval valid** (negative test); fixture workspace (30 UAV records) screened end to end through the API with HUMAN provenance on every decision | **RELEASE** (artifact identity, acceptance semantics) |
| **M1b-0 Reveal tracking** | 4 | Carried from M1a: the engine records each first reveal of a proposal (a `REVEAL` audit row, no outcome) and stamps `changed_after_reveal` on a superseding event that follows it (contract §3.1); the library `submit_proposal` refuses a proposal without model and prompt hash; `PROJECTION_STALE` becomes a typed refusal on publish and a PRISMA-preview check. | A decision changed after a reveal is stamped `changed_after_reveal: true` and journaled; one changed before the reveal is not; replay keeps bytes and approval (tests) | **RELEASE** (adds meaning to a field of stored decision events) |
| **M1b-1 Screening desktop UI** | 4–5 | UI: screening specs 01–03, 05, 08, 09 (all FINAL); desktop triage with keyboard; **you see every record by default**; proposals from the MCP path; publish with QR pairing. | Playwright: full desktop triage of the fixture workspace; proposal hidden until decision; a change after the reveal shows as such | STANDARD |
| **M1b-2 Screening drivers + eval** | 5 | One driver interface with three providers: **Anthropic** (default; Batches, caching, refusal → Unclear), **OpenAI-compatible** (base URL + key: OpenAI, OpenRouter, Azure, Ollama, vLLM, LM Studio; structured output where supported, else schema-checked, a failed check → Unclear), **Gemini** (moved behind the interface); keys in the OS keychain; per-provider consent; screening task with its eval (agent-system §5); specs 06–07; measured cost per 1,000 records. | Prompt-gate eval passes on the human-confirmed v03 set for the default provider and model; every provider passes the same driver contract tests on recorded responses | STANDARD |
| **M2 Screening mobile** | 5 | Spec 04 final; swipe card, reason sheet, undo, IndexedDB queue + replay; `--lan` serves a **restricted sub-app** (screening reads and decision events only, never jobs/pipelines) with short-lived phone tokens; WebKit mobile emulation | Playwright: 30 decisions on a mobile viewport with the network cut mid-run, all replayed once; a conflict is surfaced; jobs/pipelines unreachable over LAN (test); a real phone on LAN is used by you | STANDARD |
| **M5-slim Package (ship)** | 6 | Static export served by FastAPI; `nexus-scholar ui`; `.mcpb`; wheel smoke with the UI; honest "not production" labels (§8); **decision export** (RIS/CSV); **methods paragraph** with PRISMA counts and an automation-use statement; one-page **data-flow statement** (what leaves the machine, to which provider); delete `scholar_bib` | **The gate:** a fresh install from the wheel; accept-corpus → screening → publish on the golden UAV workspace by you, with the audit trail intact; CI matrix green | **RELEASE** (closure) |
| **M3 Discovery** (stretch) | 7–8 | Full Packet B adoption at runtime (CORE-07); CORE-06/10; SRCH-30/11/31/12/13/14/10; CORE-21 legs in the journal; VCR cassettes for the golden search; agent tasks: query critique, near-twin, methods text. UI: discovery specs 01–08. | Live search on the golden protocol, frozen to cassettes; PRISMA-S report lists the executed string, total, fetched and cap per database; a re-run produces identical ids | **RELEASE** (Packet B) |
| **M4 Inception web** (after the horizon) | — | INC-08/09/21/22, PROT-02, PROT-08 (PROT-01 relabelled advisory); multi-workspace server; stateless step API; recon over HTTP; agent tasks and chat; UI: inception specs 00–08. Until then, inception runs through the CLI/MCP wizard, labelled beta. | Golden workspace re-created in the web wizard; re-inception refuses without `--replace` | **RELEASE** |

**Before M2 starts:** five interviews with labs or institutions (see the `product-direction-sellable` direction), to test what stage 1 sells.

---

## 7. Risks and cuts

**Risks**
- **M1a is the critical path.** It is RELEASE and carries the decision-event and identity changes. It was split from the UI work for that reason; if it slips, M2 moves, not M5-slim's scope.
- **Packet B adoption may surface contract drift.** That is `BLOCKED_BASELINE_DRIFT`: stop and decide, never regenerate.
- **The phone LAN path depends on the INC-01 fix** and on Windows firewall prompts. Reload while offline needs HTTPS, which is not in stage 1.
- **Anchoring bias from showing AI proposals** is a research-method risk. The proposal is hidden until the human decides by default; the setting is recorded.
- **Privacy:** abstracts sent to an LLM provider need explicit per-provider consent on screen 06.
- **Single maintainer:** the 8-week plan has no slack.

**Cut first → last**
1. M3 Discovery UI (already stretch); keep `accept-corpus` and import as the entry path. (Web inception is already past the horizon.)
2. The in-app Calibrate screen. The prompt-gate eval on the v03 labelled set stays.
3. Dedup near-twin review UI. Show counts only.
4. Tauri and anything desktop (already stage 2).
5. fr/ar for new strings. They fall back to en, visibly.
6. Live harvest SSE. A batch job plus a report is enough.
7. **Never cut:** the screening P0s, decision provenance, the offline queue, the golden run.

---

## 8. Parked, labelled honestly

- **UI:** `corpus`, `lineage` and `audit` stay. `audit` is in scope because it carries provenance. Any route or panel touching synthesis, matrix, graph, RoB/trust or full-text shows a visible "Not production — parked" banner (a shared `ParkedNotice` component), never a silent removal.
- **Docs:** `docs/kits_surface_matrix.md` and the user guide mark `scholar_rag`, `scholar_graph`, `scholar_verify` and full-text (`scholar_pdf`, PDF-07/08) as parked.
- **CLI:** `--help` for parked commands prints a one-line "parked, not production" notice.
- **MCP:** parked tools return a typed refusal or a warning field.

---

## 9. Questions for you before implementation

**Answered 2026-11-03:**
1. C staged from A0.
2. Both paths, MCP first. No hosted token resale.
3. The full 2-month plan (the 1-month cut stays the fallback in §7).
4. The brand book wins.

Still open: which paid feature gets built first in stage 2. It is decided by user demand, not now.

Original questions:

1. **Deployment:** do you confirm C staged from A0 (§5.3)? Is terminal install (`uv tool install`) acceptable for the first users, or must a double-click installer ship in month 1?
2. **AI default:** your own Claude subscription through MCP, a BYO API key in the UI, or both? Should hosted token resale stay permanently out?
3. **First coded paid feature (stage 2):** sync/multi-device, or team dual screening with κ? Must sync be end-to-end encrypted?
4. **Horizon:** the 1-month screening-wedge cut (§6), or the full 2-month plan?
5. **Theme:** the brand book replaces VISUAL_DIRECTION (§3)?
