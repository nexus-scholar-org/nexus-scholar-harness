# UI-07 Action Specification (minimal, separately reviewed)

Status: specification-in-review. No implementation authorized by this document.
Companion: [UI-07 Presentation Spec](./UI-07_PRESENTATION_SPEC.md) (read-only; this spec adds nothing to it).
HCM prerequisite: [HCM-02 disposition](../harness-core-modularity/hcm-02-disposition.md).
Product direction: [individual researcher application](../decisions/individual-researcher-product.md).
Requesting packet: [AGENT_WORK_PACKETS.md](./AGENT_WORK_PACKETS.md) §UI-07.

All example payloads in this document are **illustrative** and use
obviously-synthetic values (`WSP-EXAMPLE-*`, `RUN-EXAMPLE`). They assert
nothing about any real workspace.

## 1. Scope: the smallest action set that completes the UI-04 journey

The UI-04 screen (GATES §8) collects a researcher's decision + reason per
study but its submit is disabled "until the API exists". This spec defines
the **only** operations that enable that journey, reusing the merged AG-04
services (`authority.review`, worker `recommendation`, AG-03C generation
gate) with the AG-03C gate itself **untouched**:

1. **Draft review capture** — store the researcher's in-progress
   resolutions as an explicitly-labeled NON-authoritative draft.
2. **Override-as-draft** — record a researcher change against the worker
   recommendation as draft content (never as an approval).
3. **Defer / cancel drafts** — record a deferred/cancelled state with
   reason; publishes nothing (AG-04 `defer_command` semantics).
4. **Approval request** — researcher asks the operator to approve exactly
   the reviewed revision (pairing-code scheme, §3).
5. **Publication trigger** — authorized collect only: the existing
   AG-03C `publish_generation` gate runs unchanged; the browser never
   writes publication outputs.

What exists today and stays as-is: `POST
/api/v1/screening/batch/{n}/decisions` writes **draft** decision files
only (rejects unknown ids with 422; exact-coverage and unresolved-row
gates run at approve/collect, not at draft; logs `SCREEN_DECISIONS`);
agent decision files are **worker input** consumed by `cmd_collect`; the
CLI `review`/`approve`/`defer`/`recommend` commands remain the
authoritative operator surface. Neither the console POST nor agent
decision files mint approval — §6 names them as non-bypass surfaces.

## 2. Threat analysis: why browser-held credentials cannot authenticate approval

This section is normative reasoning, not background. Any reviewer must be
able to follow why §3 is shaped as it is.

- **Deployment fact.** The proven AG-03/04 deployment runs the worker at
  Windows Low integrity while the operator works in a Medium terminal, and
  `approve_command` refuses when its own process token is Low
  (`review.py: _is_low_integrity_process`, `approve_command:779-784`).
  The Low-IL boundary restrains what the worker process can do, not what
  it can read at the same-user file level.
- **Bearer/session tokens are readable.** Any bearer token, session
  cookie, or long-lived API secret the browser holds is reachable by the
  same-user worker through ordinary file reads (browser profile storage,
  config files) and, on Windows, through DPAPI-protected blobs the user's
  own processes can unprotect. A Low-IL worker that can read the token
  can present it: possession of the token proves nothing about whether
  the operator approved.
- **Conclusion recorded.** Browser-held credentials **CANNOT**
  authenticate approval. A design that accepts "the browser sent the
  operator's token, therefore the operator approved" silently weakens
  AG-04 to browser-possession-equals-operator. This spec does not do
  that. Approval authority comes ONLY from the publisher-owned operator
  context (`literature/screening/operator_context.json` via
  `load_operator_context`) plus a fresh operator act in a Medium
  terminal — never from a name, role string, reviewer field, editable
  JSON file, or HTTP credential.

## 3. Primary scheme: pairing-code approval

The operator act happens where the authority already lives (their Medium
terminal); the browser only carries a short, single-use, time-bound code
that is useless to anyone who did not see the terminal.

### 3.1 Flow

1. Operator runs `approve --begin --batch <n>` in their Medium terminal.
   The server freezes the exact review snapshot (AG-03B single-buffer
   discipline: parse, hash, and display read identical bytes), stages a
   **pending review** record bound to the snapshot hash, and prints a
   single-use time-bound code (illustrative format `EXAMPLE-123456`).
   The code MUST be drawn from a server-side CSPRNG secret of ≥128-bit
   entropy, MUST be single-use, MUST expire no later than 10 minutes
   after minting, MUST be verified with a constant-time comparison
   against the stored hash (§3.6), and MUST be verified behind a
   rate-limited endpoint with a bounded attempt count. Exact parameters
   above these floors (alphabet, lifetime within the cap, attempt
   budget) are fixed at implementation review — but values below these
   floors are refused: a weaker configuration is a review failure, not a
   tuning choice.
2. Operator reads the code from their own terminal and types it into the
   browser approval dialog (which shows the same snapshot fingerprint the
   terminal printed, so a mismatched view is visible before typing).
3. Server verifies: code exists, is unexpired, is unused, and the staged
   snapshot is still current (bytes unchanged, parents unchanged,
   generation gate would still resolve). On success the server mints the
   approval **via the existing AG-03B path** (`mint_approval` /
   `mint_publication_approval` with the publisher-owned operator
   identity) and marks the code consumed. The worker cannot see terminal
   output, cannot guess the code, and replay is useless (single-use +
   snapshot-bound: a replayed code against changed content fails the
   still-current check).

**Pending-store secrecy (normative).** The pending-approval store holds
ONLY a salted hash of the pairing code — never the plaintext, never a
reversibly-encrypted copy. Verification compares in constant time
against that hash. The stored record carries the snapshot fingerprint,
the expiry, and an attempt counter only. Codes never appear in the
audit journal, the workspace index, or any other audit surface (the
journal records the minted approval fingerprint, never the code).
Rationale: workspace files are Low-readable per §2, so a plaintext (or
reversibly stored) code would turn an ordinary file read into code
theft; a hash-only store keeps file-read from yielding a presentable
code.

### 3.2 Content binding per action

| Action | Reviewed revision | Binding |
|---|---|---|
| Draft capture / override-as-draft | none (explicitly unapproved) | draft bytes + parent batch artifact id + author label `researcher-draft` + timestamp; draft approval fields absent, never defaulted |
| Defer / cancel drafts | the deferred batch index + reason | deferral record (`DEFERRAL_SCHEMA`) voids staged approvals for that batch (fingerprints preserved in the record); publishes nothing |
| Approval request (`--begin`) | the frozen AG-03B snapshot (recommendation bytes + final bytes + binding) | `ApprovalBinding` (workspace/run/batch/protocol/corpus/revision/policy) + `recommendation_sha256` + `final_decision_sha256` + snapshot fingerprint |
| Publication trigger | the AG-03C publication snapshot (scope + output digests) | `publication_binding` + per-output `sha256` digests; `publish_generation` re-verifies before any write |

A reviewed file that differs from the worker recommendation becomes a
superseding revision preserving the original (AG-03B `supersede`); the
fresh approval binds the new revision only. Stale approvals never
authorize changed revisions.

### 3.3 Stale-view handling

The browser view carries the snapshot fingerprint it rendered. Before
minting, the server revalidates: current file bytes still hash to the
staged snapshot; batch parents still resolve to the same registry
entries; protocol fingerprint unchanged. Any drift → the code is
invalidated, the approval is refused with a typed `STALE_VIEW` error
naming the changed element, and the UI shows "the content changed since
you reviewed it — re-review in the terminal" (not the old bytes, not an
auto-retry). Content change invalidates the code even within its time
window.

### 3.4 Concurrent-edit handling

Two competing publishers serialize on the AG-03C best-effort lock
(`.collect.lock`): the second writer **joins-or-refuses** — identical
generation (same id, outputs, approval) joins idempotently; anything
else refuses with `GENERATION_LOCKED` / scope mismatch and never mixes
generations. Two competing `--begin` codes for one batch: the first
consumed code wins; the second fails the still-current check (its staged
snapshot no longer matches) and must `--begin` again. No last-writer-wins
merge of approvals exists.

### 3.5 Approval invalidation after changes

Any post-approval change to decisions content, batch parents, protocol,
or publication outputs invalidates the staged approval at the AG-03C
gate (`APPROVAL_CONTENT_CHANGED` / `APPROVAL_SCOPE_MISMATCH` /
`GENERATION_STALE`): `require_current_generation` reports non-CURRENT
and publication outputs stop serving (Presentation Spec R6). A deferral
voids staged batch and publication approvals for that batch. Invalidation
is structural (digest/binding comparison), not a revocation list — which
is recorded as not-yet-existing (AG-03C doc: revocation/expiry
structural but vacuous until a store/policy exists).

### 3.6 Local-origin protections

The console binds loopback-only by default (`serve --host 127.0.0.1`,
`cli.py: serve`); pairing codes are accepted only over that loopback
binding, never over a remote-exposed listener. Institution-hosted or
SaaS exposure is a deferred delivery option (product decision doc) and
requires a separate architecture decision — this spec does not authorize
it. The pending-review store lives server-side in the workspace, never
in browser storage; it holds only the salted code hash plus snapshot
fingerprint, expiry, and attempt counter (§3.1) — never a plaintext or
reversibly-stored code. Codes are not logged to the audit journal (the
journal records the minted approval fingerprint, never the code), the
workspace index, or any other audit surface.

The browser holds the typed code memory-only: never in `localStorage`,
`sessionStorage`, navigation history, disk cache, or autofill stores;
the in-memory copy is cleared on submit, on consume, and on expiry; the
approval dialog POSTs the code once over loopback and retains nothing
afterwards. Rationale: §2 establishes that the Low reader reaches
browser profile storage, so any persisted code would be readable by the
very process this scheme withholds approval from.

## 4. Fallback: CLI-only approval with browser drafts

If pairing is rejected at review, the safe fallback is: the browser
captures drafts only (operations 1–3 above, explicitly labeled
NON-authoritative); **all** approval and publication happen in the
operator's terminal via the existing `approve`/`collect` commands; the
browser polls the read-only publication status (Presentation Spec §3(e))
to show the outcome. No browser credential, no code, no approval-shaped
POST exists in this fallback. Drafts remain worker input until the
operator's CLI act mints approval — the same authority posture as AG-04
today, with the browser as a drafting convenience.

## 5. Recoverable failures (what the UI displays for each)

| Failure | Code | UI display |
|---|---|---|
| No worker recommendation yet | `WORKER_BATCH_MISSING` | "No worker draft for this batch — run recommend first." |
| Batch file absent / parent unresolvable | `WORKER_BATCH_MISSING` / `WORKER_PARENT_UNRESOLVED` | "Batch unavailable — refusing to invent parents." + batch name |
| Draft references unknown study ids | `COVERAGE_INCOMPLETE` (missing/extra lists) | "Draft does not cover the batch (missing=…, extra=…)." |
| Non-terminal rows presented for approval | `UNRESOLVED_FINALIZE_REFUSED` | "Unresolved rows remain (…). Resolve to INCLUDE/EXCLUDE or defer." |
| Checklist/dual inputs in pilot | `REVIEW_CHECKLIST_UNSUPPORTED` / `REVIEW_DUAL_UNSUPPORTED` | "This input shape is out of pilot scope." |
| Missing/unreadable operator context | `OPERATOR_CONTEXT_MISSING` | "No verified operator identity — approval refused." |
| Low-integrity caller attempts approve | `APPROVAL_NOT_OPERATOR` | "Operator action refused at worker integrity level." |
| Code expired / already used / unknown | `PAIRING_CODE_INVALID` (+ `expired`/`consumed` detail) | "That code is expired/used — begin again in the terminal." |
| Content changed after `--begin` | `STALE_VIEW` | "Content changed since review — re-review before approving." |
| Concurrent publisher holds lock | `GENERATION_LOCKED` | "Another publisher is writing — retry once it finishes." |
| Approval/content drift at collect | `APPROVAL_CONTENT_CHANGED` / `APPROVAL_SCOPE_MISMATCH` | "Staged content no longer matches the approval — re-review." |
| Audit sink failure at publish | `PROMOTION_AUDIT_FAILED` | "Publication refused: provenance could not be recorded. Nothing was published." |
| Approval requested with no resolved file | `APPROVAL_MISSING` | "Nothing resolved to approve — missing approval is never default approval." |

Every failure publishes nothing; drafts and deferrals survive failures
that do not invalidate them (stale-view and invalidation failures void
only the staged approval/code, never the draft bytes).

## 6. Explicit non-claims and non-bypass surfaces

- **Never trusted:** browser-supplied name, role, reviewer string,
  editable approval/review JSON, HTTP bearer/session credential, or any
  caller-minted canonical id. Authority reads from
  `operator_context.json` + the terminal act, full stop.
- **Console `POST /screening/batch/{n}/decisions` writes drafts only.**
  It rejects unknown ids and logs `SCREEN_DECISIONS`; it does not mint, stage,
  or verify any approval, and must not gain an approval-minting
  parameter without a new authority packet.
- **Agent decision files are worker input.** Files the agent/collector
  pipeline writes are consumed by `cmd_collect` under the AG-03C gate;
  their presence never constitutes approval.
- **Neither surface above mints approval.** Any future endpoint or file
  convention that could be mistaken for approval (draft auto-promotion,
  "approve=true" flags, approval-shaped sidecars written by non-operator
  paths) is a bypass and is refused at review.
- **POSIX unproven.** The Low-IL refusal is Windows-only by construction
  (`_is_low_integrity_process` returns False off-Windows; AG-03C notes
  POSIX has no proven arrangement). No cross-platform isolation is
  claimed; POSIX deployment needs its own enforcement packet.
- **No remote/multi-user model.** Loopback-only (§3.6). Concurrent same-host
  writers are handled by join-or-refuse (§3.4); concurrent remote
  operators are out of scope.

## 7. Open questions

- **OQ-A1 — code alphabet/lifetime/attempt tuning.** Floors are fixed
  in §3.1 (server-CSPRNG secret ≥128-bit, single-use, ≤10-minute
  validity, constant-time comparison against the stored hash,
  rate-limited verification with a bounded attempt count); values below
  them are refused. Exact parameters above the floors (alphabet,
  lifetime within the cap, attempt budget) need the AG-03C owner's
  sign-off at implementation review; this spec additionally fixes
  snapshot-binding + expiry as non-negotiable.
- **OQ-A2 — pending-review store shape.** Whether the staged pending
  record is a new sidecar file or an extension of the existing review
  record needs an AG-04-owner decision (must preserve the AG-03B
  single-buffer discipline either way).
- **OQ-A3 — pairing rejected: is the fallback sufficient for the
  individual-researcher journey?** The fallback keeps full authority but
  forces a terminal round-trip per batch. Whether that friction is
  acceptable for the first connected UI-04 journey is a product-decision
  follow-up, not an authority relaxation.
- **OQ-A4 — revocation/expiry store.** AG-03C plumbs revocation
  fingerprints and max-age but enforces neither without a store/policy.
  Whether UI-07 needs either before first connection is deferred to the
  AG track.

## 8. Traceability

- SPEC-05 (action-minimality): §1 (five operations, nothing else).
- SPEC-06 (operator-auth-scheme): §2 (threat analysis) + §3 (pairing) + §4 (fallback).
- SPEC-07 (stale-view-handling): §3.3 + §5 `STALE_VIEW`.
- SPEC-08 (invalidation): §3.5 + §5 drift rows.
- SPEC-09 (recoverable-failures): §5 table.
- SPEC-11 (no-bypass-surfaces): §6.
