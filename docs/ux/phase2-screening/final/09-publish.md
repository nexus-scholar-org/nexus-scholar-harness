# 09 Publish, approval and phone pairing    Status: FINAL | Phase 2 Screening | Route `/screening/publish`; phone `/screening/connect` | Milestone M0 (redeem path fix) + M1a (preview, pairing begin) + M1b (UI) + M2 (`/lan/pair`, phone)

Boards: `Publish` (D8), `MobilePair` (M2), `MobileApprove` (M7). Contract: `screening-api-contract.md` §4, §6.

## Amended 2026-11-07 (M6-beta)
Source: `docs/roadmap/milestones/M6-beta.md` sections B and D; decisions "Details on demand" and "Published means current". The rule is in [12](12-details-disclosure.md).
- **Checks are one line each.** A pass mark (the `include` badge "Pass", text plus icon) and the check's plain name, nothing else (`screening-publish.tsx`, the `publish-checks` list). The `detail` text of passing checks moves into the Checks card's Details. A failing check keeps its count on the line, with the `blocked` badge "Fail", and the existing "Go to triage" or Protocol-changed card below it.
- **Fingerprint and digests behind Details.** The generation id, the generation fingerprint and the file digests (the "Will be written" list) are in the approval gate card's Details. The banner after publishing reads "Published" with no id. The batch file names (`batch_001` and so on) are in the Batches card's Details; its rows read "Batch n", and the approve and code-field names use "batch n".
- **PRISMA preview keeps the numbers and the reasons table** (identified, duplicates, screened, excluded with its reasons, unclear, included, not yet decided). Nothing moves out of that card.
- **Published means current.** The workspace and publication status now read `STALE` (`GENERATION_STALE`, with the number of changed studies) as soon as a decision is made after publish; Home, the Workspaces list, Export and Methods all read it from `GET /ui/publication-status` through the currentness wrapper (✓ done 2026-11-07, `src/scholar_harness/screening/currentness.py`; `tests/console/test_publication_currentness.py::test_a_decision_after_publish_makes_the_status_stale_everywhere`). This screen shows a notice above the PRISMA card, "Decisions changed after this was published ({n} studies). Approve and publish again." (`screening.publish.stale`), with `GENERATION_STALE` in Details, and the gate is the normal one for the new generation. The published files on disk are still what was published; stored files and Contract v1 do not change.
- Tests: `publish.details.test.tsx` (each check is one line with a pass or fail mark; fingerprint, digests and batch file names are inside closed `<details>` and in the DOM; the preview still shows the reasons table; a stale status shows the notice). Playwright `screening/publish.spec.ts` opens Details before asserting provenance.

## Amended 2026-11-08 (M7b-guideline)
Source: `docs/decisions.md` 2026-11-08 "Reporting follows a guideline chosen in the protocol". Only two labels change. The counts, the checks, the "Will be written" list, the five published files (`prisma_report.json` keeps its name) and the engine do not.
- **Where the guideline comes from.** `GET /api/v1/screening/settings` (✓ `screening_v1.py:325`; the fields below ✗ M7b-guideline) gains two read-only fields: `reporting` (`"prisma-2020" | "prisma-scr" | "none"`) and `reporting_source` (`"protocol" | "playbook"`). `PUT /settings` does not accept them (the guideline is set in the protocol, not on this screen). Client: `getScreeningSettings` in `apps/research-ui/lib/screening-api.ts`, type extended. No new call.
- **Preview heading.** The card heading (`id="publish-prisma"`) follows `reporting`:

| `reporting` | Key | en | fr | ar |
| :-- | :-- | :-- | :-- | :-- |
| `prisma-2020` | `prisma` (unchanged) | PRISMA 2020 screening preview | Aperçu de sélection PRISMA 2020 | معاينة فرز PRISMA 2020 |
| `prisma-scr` | `prismaScr` | PRISMA-ScR screening preview | Aperçu de sélection PRISMA-ScR | معاينة فرز PRISMA-ScR |
| `none` | `prismaNone` | Screening preview | Aperçu de sélection | معاينة الفرز |

- **Publish body.** The side-card sentence (`publishBody`) says "the PRISMA report" under `prisma-2020` and `prisma-scr` (both are PRISMA guidelines; strings unchanged). Under `none` it uses `publishBodyNone`, which names no guideline:
  - en: "Writes the included, excluded and full-text lists and the screening counts report for the approved generation."
  - fr: "Écrit les listes d'inclusions, d'exclusions et de texte intégral ainsi que le rapport des effectifs de la sélection de la génération approuvée."
  - ar: "يكتب قوائم المُدرجة والمستبعدة والنص الكامل وتقرير أعداد الفرز للجيل المعتمد."
  - The file name `prisma_report.json` stays as it is in the "Will be written" list and in Details under every guideline (it is a publication artifact the digests depend on; decision "Not chosen: renaming").
- **Spec copy keys.** `screening.publish.prisma.*` now has three heading leaves (`prisma-2020`, `prisma-scr`, `none`); `screening.publish.publishBody` gains the `none` variant. Check names, "Pass"/"Fail", "Preview · not written" and the unclear note are unchanged.
- **Fallbacks.** If `reporting` is absent (an engine older than this change) the screen reads `prisma-2020`, so today's wording stays. Loading: the heading shows the skeleton line with the card; no guideline name appears before settings answer. Offline: the last heading stays with the "as of" caption. Error: settings refusals use the existing cards; the heading falls back to the neutral `none` wording rather than guessing a guideline. Protocol-changed: the guideline is read live, so a protocol that changes it shows the new heading with the Protocol-changed card (the preview is disabled until re-bound). Mobile read-only view uses the same keys.
- **Tests.** Vitest `publish.reporting.test.tsx` (`heading_follows_prisma_2020`, `heading_follows_prisma_scr`, `heading_without_guideline_names_none`, `publish_body_names_screening_counts_report_under_none`, `absent_reporting_reads_prisma_2020`; the same three headings render in en, fr and ar). Python `tests/console/test_screening_v1_api.py::test_settings_report_reporting_and_source_read_only` (✗ M7b-guideline: playbook default per `playbook_type`, protocol override, `PUT` ignores or refuses the fields, `reporting_source` is `protocol` or `playbook`).

**Purpose.** Check the PRISMA screening preview, approve this exact generation once on the desktop, publish; and connect a phone for screening.

**Changed from the canvas.**
- **Approval is desktop-only in stage 1** (contract §4, maintainer decision). `MobileApprove` (M7) is changed: the phone shows the PRISMA preview, the "Will be written on the desktop" list and an "Approve on your desktop" message. The pairing-code field and the "Approve and publish" button are removed from the phone. The D8 QR "Scan to approve on your phone, or type the code here" is removed; the gate keeps the code to type. The MobileHome tab "Approve" opens this read-only view.
- `MobilePair` text "approve a batch generation with the pairing code" under "This phone can" is removed; it reads "Triage records · pick an exclusion reason · undo".
- "Sample check of agreed exclusions · 60 checked · 0 wrong" is shown only when the AI-agreed-exclusion opt-in was on; otherwise the check row reads "You decided every record".
- The PRISMA box has no "agreed by the agent" exclusions unless the opt-in was on. The methods paragraph carries the automation-use statement (disclosure of agent use, queue ordering, and opt-in).
- "Agreement with the agent report attached" shows concordance, never kappa.
- "Unclear, to full text" (94) is stored `MAYBE` and is written into `included.json` with `screening.decision = "MAYBE"`; there is no `fulltext_queue.json` (the D8 file row and note are removed; researcher, 2026-11-05, spec 10 decision 6). The unclear export on `/screening/export` (spec 10) is the full-text list, linked from this screen once the status is CURRENT.
- Check "Conflicts between devices resolved" blocks Publish while any study has an open conflict.

## Entry / exit
- Entry: step bar "5 Publish" when all records are decided; Agreement link. Phone: first run opens the connect screen.
- Exit: published → 01 with a CURRENT publication status; a later decision turns it `STALE` (amendment). Gate: Approve needs the pairing code and refuses without it (`APPROVAL_MISSING`).

## Data in
| Field | Source |
| :-- | :-- |
| `{identified, duplicates_removed, screened, excluded{total, by_reason}, unclear_to_full_text, included, not_yet_decided}` | `GET /prisma/preview` ✗ M1a (desktop, phone) |
| `checks[{name, ok, detail}]` (HUMAN provenance, no open conflicts, batches bound, sample audit if opt-in, agreement attached) | `GET /prisma/preview` ✗ M1a |
| publication status (`CURRENT`, or `STALE` after a later decision) | `getPublicationStatus` ✓ `screening-api.ts:335` (currentness wrapper ✓ done 2026-11-07) |
| pairing state, expiry, attempts | `GET /actions/pairing/status` ✓ `screening.py:1407` (desktop, phone read-only) |
| batch review state | `GET /ui/batch/{n}/review` ✓ `screening.py:839` |
| conflicts | `GET /decisions/conflicts` ✗ M1a |

## Data out
- Approve (desktop only): `POST /actions/pairing/begin` ✗ M1a (`{batch}` → `{code_expires_at, code_shown_on: "terminal"}`); the code appears only in the terminal running the console, and the researcher types it here (decision 2026-11-04: no code or QR over HTTP); then `POST /actions/pairing/redeem` ✓ `screening.py:1429` with the typed code; then `POST /actions/publish` ✓ `screening.py:1581`. Journal: approval with generation fingerprint and device; publish. A decision after approval invalidates it visibly.
- Defer: `POST /actions/defer` ✓ `screening.py:1512` with a reason.
- Phone pairing: desktop calls `POST /lan/session/begin` ✗ M2 (on Home, 01) and shows the QR (URL plus one-time token, valid 2 minutes, single use); phone calls `POST /lan/pair` ✗ M2 with `{one_time_token}`, receiving a session cookie (phone scope); expired or reused tokens are refused with `TOKEN_SCOPE_REFUSED`. The session ends at `POST /lan/session/stop` ✗ M2, when the desktop `nexus-scholar ui` process stops, or after 12 hours. Nothing goes in URLs after first load.
- **Changed from the canvas (session text):** "valid until you close the app" (M1 Connected card, MobilePair, D1) becomes "code valid 2 minutes, one use; session ends when you stop phone access, when the desktop app exits, or after 12 hours".

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/screening/actions/pairing/status` | ✓ `screening.py:1407` |
| `POST /api/v1/screening/actions/pairing/redeem` | ✓ `screening.py:1429` (desktop only; M0 fixes the proxy allowlist path) |
| `POST /api/v1/screening/actions/defer` | ✓ `screening.py:1512` |
| `POST /api/v1/screening/actions/publish` | ✓ `screening.py:1581` |
| `GET /api/v1/screening/ui/batch/{n}/review` | ✓ `screening.py:839` |
| `GET /api/v1/screening/prisma/preview` | ✗ M1a |
| `POST /api/v1/screening/actions/pairing/begin` | ✗ M1a |
| `GET /api/v1/screening/decisions/conflicts` | ✗ M1a |
| `POST /api/v1/screening/lan/session/begin`, `POST /api/v1/screening/lan/session/stop` | ✗ M2 |
| `POST /api/v1/screening/lan/pair` | ✗ M2 |

## States
- **Default (D8)**: h1 "All 3,241 records are decided. Approve this generation to publish the screening." PRISMA 2020 preview card (badge "Preview · not written"): identified, duplicates removed, screened, reports sought, excluded with reasons table, note that unclear records are kept in `included.json` as "Unclear, to full text". Checks card (one line per check, amendment). Side: "Will be written" list (the five published files `included.json`, `excluded.json`, `conflicts.json`, `prisma_screening_report.md`, `prisma_report.json`, plus `generation.json`; no `fulltext_queue.json`; digests in Details), gate panel (code field, "Approve and publish" brand, "Defer with a reason"; the generation fingerprint is in its Details), and the phone card (QR) from 01.
- **Empty**: nothing decided → Publish disabled, link to 03.
- **Loading**: skeleton PRISMA cards; publish shows job status.
- **Error**: `APPROVAL_MISSING` (✓ `src/scholar_harness/authority/binding.py:42`), `PAIRING_CODE_INVALID` (✓ `src/scholar_harness/authority/pairing.py:65`), `APPROVAL_NOT_OPERATOR` (✓ `src/scholar_harness/authority/binding.py:43`), `COVERAGE_INCOMPLETE` (✓ `src/scholar_harness/screening/integrity.py:20`), `UNRESOLVED_FINALIZE_REFUSED` (✓ `integrity.py:24`), `STALE_BINDING` (✓ `integrity.py:28`), `ACTION_ORIGIN_REFUSED` (✓ `screening.py:1319`), `BATCH_INCOMPLETE` (conflicted study left out of the projection), `TOKEN_SCOPE_REFUSED` (phone connect), `ENGINE_UNREACHABLE` (client-side).
- **Partial**: `not_yet_decided` > 0 → Publish disabled; preview marked "n not yet decided".
- **Offline**: last preview with "as of" caption; approve, publish and QR disabled. Phone: preview from cache, "Approve on your desktop" stays.
- **Protocol-changed**: Publish disabled with the Protocol-changed card (08); approval of the old generation shown as superseded.
- **Published, decisions since** (new): `STALE` notice above the preview (amendment); Approve and publish for the new generation as usual. Cannot occur before a first publish.
- **Phone (M7, changed)**: PRISMA summary (identified, screened after duplicates, excluded with a reason, included, unclear to full text), "Exclusion reasons and checks" link, "Will be written on the desktop", message "Approve on your desktop", "This phone has n queued decisions".
- **Connect (M2)**: "Connect this phone to your desktop." camera view, manual code field, "This phone can / cannot" card, button "Connect". After success → Home. Failure → `TOKEN_SCOPE_REFUSED` with "Show the pairing QR again on the desktop".

## Desktop layout
`Publish` (D8): split. Main: PRISMA preview, Checks. Side: Will be written, Approval gate (brand-soft, dashed brand border; one brand button). Phone connection QR lives on Home (01); no QR on the gate.

## Mobile layout (≤ 640 px)
`MobilePair` and the read-only `MobileApprove`: 390 x 844, primary 44 px+, no approve action. `inputmode=numeric` and `autocomplete=one-time-code` on the connect code field.

## Keyboard
Desktop order: PRISMA, checks, files, code field, Approve, Defer. `Enter` in the code field opens a confirm dialog. Phone: external keyboard `Tab` through the summary.

## Copy
`screening.publish.title`, `screening.publish.lede`, `screening.publish.prisma.*`, `screening.publish.checks.*` (plus `screening.publish.check.pass|fail`), `screening.publish.published` ("Published"), `screening.publish.batch.n` ("Batch {n}"), `screening.publish.stale` ("Decisions changed after this was published ({n} studies). Approve and publish again."), `screening.details.*` (12), `screening.publish.files`, `screening.publish.gate.{label,body,code,approve,defer}`, `screening.publish.mobile.approveOnDesktop`, `screening.publish.methods.automation`, `screening.pair.{title,body,scan,manualCode,canDo,cannot,connect}`, `screening.outcome.unclear.long`.

## Accessibility
QR has a text alternative (the URL and code spelled out on request). Checks use text plus `include` / `blocked` roles. Code field is labelled. RTL: fingerprints and codes LTR; layout mirrors.

## Acceptance tests
Vitest: `publish.details.test.tsx` (M6-beta), `publish.conflict-blocks.test.tsx`, `publish.mobile-has-no-approve.test.tsx`, `pairing.exchange.test.ts`. Playwright: `screening/publish.spec.ts` (approve with the code, publish golden-uav-30, `APPROVAL_MISSING`), `screening/pair-phone.spec.ts` (token exchange, reuse refused with `TOKEN_SCOPE_REFUSED`, publish route unreachable over LAN).

## Decisions
1. Contract §9.1 (decided 2026-11-04): a fresh one-time approval code per batch generation, never the pairing code. Approve and publish stays disabled while any paired phone has queued events, with the message "A phone still has unsent decisions. Open it on the same network to send them."
