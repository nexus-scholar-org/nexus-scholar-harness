# 09 Publish, approval and phone pairing    Status: DRAFT | Phase 2 Screening | Route `/screening/publish`; phone `/screening/connect` | Milestone M0 (redeem path fix) + M1a (preview, pairing begin) + M1b (UI) + M2 (`/lan/pair`, phone)

Boards: `Publish` (D8), `MobilePair` (M2), `MobileApprove` (M7). Contract: `screening-api-contract.md` §4, §6.

**Purpose.** Check the PRISMA screening preview, approve this exact generation once on the desktop, publish; and connect a phone for screening.

**Changed from the canvas.**
- **Approval is desktop-only in stage 1** (contract §4, maintainer decision). `MobileApprove` (M7) is changed: the phone shows the PRISMA preview, the "Will be written on the desktop" list and an "Approve on your desktop" message. The pairing-code field and the "Approve and publish" button are removed from the phone. The D8 QR "Scan to approve on your phone, or type the code here" is removed; the gate keeps the code to type. The MobileHome tab "Approve" opens this read-only view.
- `MobilePair` text "approve a batch generation with the pairing code" under "This phone can" is removed; it reads "Triage records · pick an exclusion reason · undo".
- "Sample check of agreed exclusions · 60 checked · 0 wrong" is shown only when the AI-agreed-exclusion opt-in was on; otherwise the check row reads "You decided every record".
- The PRISMA box has no "agreed by the agent" exclusions unless the opt-in was on. The methods paragraph carries the automation-use statement (disclosure of agent use, queue ordering, and opt-in).
- "Agreement with the agent report attached" shows concordance, never kappa.
- "Unclear, to full text" (94) goes to `fulltext_queue.json` (stored `MAYBE`).
- Check "Conflicts between devices resolved" blocks Publish while any study has an open conflict.

## Entry / exit
- Entry: step bar "5 Publish" when all records are decided; Agreement link. Phone: first run opens the connect screen.
- Exit: published → 01 with a CURRENT publication status. Gate: Approve needs the pairing code and refuses without it (`APPROVAL_MISSING`).

## Data in
| Field | Source |
| :-- | :-- |
| `{identified, duplicates_removed, screened, excluded{total, by_reason}, unclear_to_full_text, included, not_yet_decided}` | `GET /prisma/preview` ✗ M1a (desktop, phone) |
| `checks[{name, ok, detail}]` (HUMAN provenance, no open conflicts, batches bound, sample audit if opt-in, agreement attached) | `GET /prisma/preview` ✗ M1a |
| publication status | `getPublicationStatus` ✓ `screening-api.ts:335` |
| pairing state, expiry, attempts | `GET /actions/pairing/status` ✓ `screening.py:1407` (desktop, phone read-only) |
| batch review state | `GET /ui/batch/{n}/review` ✓ `screening.py:839` |
| conflicts | `GET /decisions/conflicts` ✗ M1a |

## Data out
- Approve (desktop only): `POST /actions/pairing/begin` ✗ M1a (`{generation}` → `{qr_payload, code_expires_at}`) shows the code; then `POST /actions/pairing/redeem` ✓ `screening.py:1429` with the typed code; then `POST /actions/publish` ✓ `screening.py:1581`. Journal: approval with generation fingerprint and device; publish. A decision after approval invalidates it visibly.
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
- **Default (D8)**: h1 "All 3,241 records are decided. Approve this generation to publish the screening." PRISMA 2020 preview card (badge "Preview · not written"): identified, duplicates removed, screened, reports sought, excluded with reasons table, note on `fulltext_queue.json`. Checks card. Side: "Will be written" list, gate panel (generation fingerprint, code field, "Approve and publish" brand, "Defer with a reason"), and the phone card (QR) from 01.
- **Empty**: nothing decided → Publish disabled, link to 03.
- **Loading**: skeleton PRISMA cards; publish shows job status.
- **Error**: `APPROVAL_MISSING` (✓ `src/scholar_harness/authority/binding.py:42`), `PAIRING_CODE_INVALID` (✓ `src/scholar_harness/authority/pairing.py:65`), `APPROVAL_NOT_OPERATOR` (✓ `src/scholar_harness/authority/binding.py:43`), `COVERAGE_INCOMPLETE` (✓ `src/scholar_harness/screening/integrity.py:20`), `UNRESOLVED_FINALIZE_REFUSED` (✓ `integrity.py:24`), `STALE_BINDING` (✓ `integrity.py:28`), `ACTION_ORIGIN_REFUSED` (✓ `screening.py:1319`), `BATCH_INCOMPLETE` (conflicted study left out of the projection), `TOKEN_SCOPE_REFUSED` (phone connect), `ENGINE_UNREACHABLE` (client-side).
- **Partial**: `not_yet_decided` > 0 → Publish disabled; preview marked "n not yet decided".
- **Offline**: last preview with "as of" caption; approve, publish and QR disabled. Phone: preview from cache, "Approve on your desktop" stays.
- **Protocol-changed**: Publish disabled with the Protocol-changed card (08); approval of the old generation shown as superseded.
- **Phone (M7, changed)**: PRISMA summary (identified, screened after duplicates, excluded with a reason, included, unclear to full text), "Exclusion reasons and checks" link, "Will be written on the desktop", message "Approve on your desktop", "This phone has n queued decisions".
- **Connect (M2)**: "Connect this phone to your desktop." camera view, manual code field, "This phone can / cannot" card, button "Connect". After success → Home. Failure → `TOKEN_SCOPE_REFUSED` with "Show the pairing QR again on the desktop".

## Desktop layout
`Publish` (D8): split. Main: PRISMA preview, Checks. Side: Will be written, Approval gate (brand-soft, dashed brand border; one brand button). Phone connection QR lives on Home (01); no QR on the gate.

## Mobile layout (≤ 640 px)
`MobilePair` and the read-only `MobileApprove`: 390 x 844, primary 44 px+, no approve action. `inputmode=numeric` and `autocomplete=one-time-code` on the connect code field.

## Keyboard
Desktop order: PRISMA, checks, files, code field, Approve, Defer. `Enter` in the code field opens a confirm dialog. Phone: external keyboard `Tab` through the summary.

## Copy
`screening.publish.title`, `screening.publish.lede`, `screening.publish.prisma.*`, `screening.publish.checks.*`, `screening.publish.files`, `screening.publish.gate.{label,body,code,approve,defer}`, `screening.publish.mobile.approveOnDesktop`, `screening.publish.methods.automation`, `screening.pair.{title,body,scan,manualCode,canDo,cannot,connect}`, `screening.outcome.unclear.long`.

## Accessibility
QR has a text alternative (the URL and code spelled out on request). Checks use text plus `include` / `blocked` roles. Code field is labelled. RTL: fingerprints and codes LTR; layout mirrors.

## Acceptance tests
Vitest: `publish.conflict-blocks.test.tsx`, `publish.mobile-has-no-approve.test.tsx`, `pairing.exchange.test.ts`. Playwright: `screening/publish.spec.ts` (approve with the code, publish golden-uav-30, `APPROVAL_MISSING`), `screening/pair-phone.spec.ts` (token exchange, reuse refused with `TOKEN_SCOPE_REFUSED`, publish route unreachable over LAN).

## Open questions
1. Contract §9.1: approval code reuse (phone-pairing code or a fresh one-time code per generation), and must every paired phone report zero queued events before approval (canvas notes q3 and q7)?
